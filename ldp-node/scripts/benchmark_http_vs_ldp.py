#!/usr/bin/env python3
"""Benchmark matrix transfer over plain HTTP/JSON versus LDP/gRPC."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import request

from generated import ldp_service_pb2
from logging_utils import configure_logging
from network.queue import clear_queue, enqueue_payload
from network.receiver import create_server
from network.transmitter import transmit_payloads


LOGGER = logging.getLogger("benchmark")


@dataclass(frozen=True)
class BenchmarkResult:
    protocol: str
    matrix_count: int
    rows: int
    cols: int
    total_floats: int
    total_bytes: int
    duration_seconds: float


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def build_matrix_payloads(matrix_count: int, rows: int, cols: int) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    flat_size = rows * cols

    for matrix_index in range(matrix_count):
        tensor_data = [
            float(((matrix_index * flat_size) + element_index) % 1024) / 1024.0
            for element_index in range(flat_size)
        ]
        payloads.append(
            {
                "token_index": matrix_index,
                "tensor_data": tensor_data,
                "tensor_shape": [rows, cols],
                "target_next_layer": 1,
            }
        )

    return payloads


def build_grpc_payloads(payloads: Sequence[dict[str, Any]]) -> list[ldp_service_pb2.ActivationPayload]:
    return [
        ldp_service_pb2.ActivationPayload(
            token_index=payload["token_index"],
            tensor_data=payload["tensor_data"],
            tensor_shape=payload["tensor_shape"],
            target_next_layer=payload["target_next_layer"],
        )
        for payload in payloads
    ]


class MatrixHTTPHandler(BaseHTTPRequestHandler):
    server: "MatrixHTTPServer"

    def do_POST(self) -> None:  # noqa: N802
        started_at = time.perf_counter()
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        payload = json.loads(body)
        payloads = payload["payloads"]

        for item in payloads:
            enqueue_payload(item)

        duration = time.perf_counter() - started_at
        self.server.received_payloads = len(payloads)
        self.server.received_bytes = content_length
        self.server.request_duration_seconds = duration
        LOGGER.info(
            "HTTP receiver accepted %s matrix payload(s), bytes=%s, request_duration=%.4fs",
            len(payloads),
            content_length,
            duration,
        )

        response_body = json.dumps({"status_success": True, "error_message": ""}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.debug("HTTP server: " + format, *args)


class MatrixHTTPServer(ThreadingHTTPServer):
    received_payloads: int = 0
    received_bytes: int = 0
    request_duration_seconds: float = 0.0


def run_http_benchmark(payloads: Sequence[dict[str, Any]]) -> BenchmarkResult:
    clear_queue()
    port = _find_free_port()
    server = MatrixHTTPServer(("127.0.0.1", port), MatrixHTTPHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    request_payload = json.dumps({"payloads": payloads}, separators=(",", ":")).encode("utf-8")
    started_at = time.perf_counter()

    try:
        http_request = request.Request(
            f"http://127.0.0.1:{port}/forward",
            data=request_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request) as response:
            response_body = json.loads(response.read().decode("utf-8"))
            if not response_body["status_success"]:
                raise RuntimeError(f"HTTP receiver returned an error: {response_body['error_message']!r}")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    duration = time.perf_counter() - started_at
    return BenchmarkResult(
        protocol="http",
        matrix_count=len(payloads),
        rows=payloads[0]["tensor_shape"][0],
        cols=payloads[0]["tensor_shape"][1],
        total_floats=sum(len(payload["tensor_data"]) for payload in payloads),
        total_bytes=len(request_payload),
        duration_seconds=duration,
    )


def run_ldp_benchmark(payloads: Sequence[dict[str, Any]]) -> BenchmarkResult:
    clear_queue()
    grpc_payloads = build_grpc_payloads(payloads)
    port = _find_free_port()
    server = create_server()
    bound_port = server.add_insecure_port(f"127.0.0.1:{port}")
    if bound_port == 0:
        raise RuntimeError(f"Failed to bind LDP benchmark receiver to 127.0.0.1:{port}.")
    server.start()
    logging.getLogger("network.receiver").setLevel(logging.WARNING)

    serialized_bytes = sum(payload.ByteSize() for payload in grpc_payloads)
    started_at = time.perf_counter()

    try:
        response = transmit_payloads(grpc_payloads, target=f"127.0.0.1:{port}")
        if not response.status_success:
            raise RuntimeError(f"LDP receiver returned an error: {response.error_message!r}")
    finally:
        server.stop(grace=None)

    duration = time.perf_counter() - started_at
    return BenchmarkResult(
        protocol="ldp",
        matrix_count=len(payloads),
        rows=payloads[0]["tensor_shape"][0],
        cols=payloads[0]["tensor_shape"][1],
        total_floats=sum(len(payload["tensor_data"]) for payload in payloads),
        total_bytes=serialized_bytes,
        duration_seconds=duration,
    )


def render_results(http_result: BenchmarkResult, ldp_result: BenchmarkResult) -> str:
    difference_seconds = http_result.duration_seconds - ldp_result.duration_seconds
    speedup = http_result.duration_seconds / ldp_result.duration_seconds if ldp_result.duration_seconds else float("inf")

    return "\n".join(
        [
            f"Matrix workload: count={http_result.matrix_count}, shape={http_result.rows}x{http_result.cols}, total_floats={http_result.total_floats}",
            f"HTTP: duration={http_result.duration_seconds:.4f}s bytes={http_result.total_bytes}",
            f"LDP: duration={ldp_result.duration_seconds:.4f}s bytes={ldp_result.total_bytes}",
            f"Difference: HTTP-LDP={difference_seconds:.4f}s speedup={speedup:.2f}x",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark matrix transfer over HTTP and LDP")
    parser.add_argument("--matrix-count", type=int, default=24)
    parser.add_argument("--rows", type=int, default=256)
    parser.add_argument("--cols", type=int, default=256)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging("benchmark")
    LOGGER.info(
        "Preparing benchmark payloads matrix_count=%s rows=%s cols=%s",
        args.matrix_count,
        args.rows,
        args.cols,
    )

    payloads = build_matrix_payloads(args.matrix_count, args.rows, args.cols)
    http_result = run_http_benchmark(payloads)
    ldp_result = run_ldp_benchmark(payloads)
    summary = render_results(http_result, ldp_result)
    LOGGER.info("\n%s", summary)
    print(summary)


if __name__ == "__main__":
    main()
