"""gRPC receiver implementation for the LDP worker node."""

from __future__ import annotations

import logging
from concurrent import futures

import grpc

from config.settings import get_settings
from generated import ldp_service_pb2, ldp_service_pb2_grpc
from network.queue import enqueue_payload


LOGGER = logging.getLogger(__name__)


class LLMPipelineReceiver(ldp_service_pb2_grpc.LLMPipelineServiceServicer):
    """Receives activation payload streams and forwards them into a queue."""

    def ForwardActivationStream(self, request_iterator, context):
        received_count = 0

        for payload in request_iterator:
            enqueue_payload(payload)
            received_count += 1
            LOGGER.info(
                "Queued activation payload token_index=%s target_next_layer=%s",
                payload.token_index,
                payload.target_next_layer,
            )

        LOGGER.info("Completed activation stream with %s payload(s).", received_count)
        return ldp_service_pb2.ForwardResponse(
            status_success=True,
            error_message="",
        )


def create_server() -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    ldp_service_pb2_grpc.add_LLMPipelineServiceServicer_to_server(LLMPipelineReceiver(), server)
    return server


def serve() -> None:
    settings = get_settings()
    server = create_server()
    server.add_insecure_port(settings.receiver_address)
    server.start()
    LOGGER.info("Receiver listening on %s", settings.receiver_address)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    serve()
