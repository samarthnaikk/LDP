from __future__ import annotations

import os
import socket
import threading

import pytest

from generated import ldp_service_pb2
from network.queue import clear_queue, get_queue
from network.receiver import LLMPipelineReceiver, create_server
from network.transmitter import build_mock_payloads, transmit_mock_activation


def _find_free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            return int(sock.getsockname()[1])
    except PermissionError as exc:
        pytest.skip(f"Local socket binding is not permitted in this environment: {exc}")


def test_receiver_enqueues_payloads_and_returns_success():
    clear_queue()
    servicer = LLMPipelineReceiver()

    response = servicer.ForwardActivationStream(iter(build_mock_payloads()), context=None)

    queued_payload = get_queue().get_nowait()
    get_queue().task_done()
    assert response.status_success is True
    assert response.error_message == ""
    assert queued_payload.token_index == 0
    assert list(queued_payload.tensor_data) == [pytest.approx(0.104), pytest.approx(0.105)]


@pytest.mark.timeout(5)
def test_queue_does_not_block_under_high_frequency_drops():
    clear_queue()
    payload_count = 1000
    drained = []

    def producer() -> None:
        for index in range(payload_count):
            get_queue().put_nowait(
                ldp_service_pb2.ActivationPayload(
                    token_index=index,
                    tensor_data=[0.1, 0.2],
                    tensor_shape=[2],
                    target_next_layer=1,
                )
            )

    def consumer() -> None:
        while len(drained) < payload_count:
            item = get_queue().get(timeout=1)
            drained.append(item.token_index)
            get_queue().task_done()

    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)
    consumer_thread.start()
    producer_thread.start()
    producer_thread.join()
    consumer_thread.join()

    assert len(drained) == payload_count
    assert drained[0] == 0
    assert drained[-1] == payload_count - 1


@pytest.mark.timeout(5)
def test_transmitter_and_receiver_integrate_over_grpc():
    clear_queue()
    server = create_server()
    port = _find_free_port()
    try:
        bound_port = server.add_insecure_port(f"127.0.0.1:{port}")
    except RuntimeError as exc:
        pytest.skip(f"gRPC server binding is not available in this environment: {exc}")
    if bound_port == 0:
        pytest.skip("gRPC server did not receive a bindable local port in this environment.")
    server.start()

    os.environ["LDP_TRANSMITTER_HOST"] = "127.0.0.1"
    os.environ["LDP_TRANSMITTER_PORT"] = str(port)

    try:
        response = transmit_mock_activation()
        queued_payload = get_queue().get(timeout=1)
        get_queue().task_done()
        assert response.status_success is True
        assert queued_payload.target_next_layer == 1
    finally:
        server.stop(grace=None)
        os.environ.pop("LDP_TRANSMITTER_HOST", None)
        os.environ.pop("LDP_TRANSMITTER_PORT", None)
        clear_queue()
