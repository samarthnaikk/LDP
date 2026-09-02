"""gRPC transmitter implementation for the LDP master node."""

from __future__ import annotations

import logging
from typing import Iterable

import grpc

from config.settings import get_settings
from generated import ldp_service_pb2, ldp_service_pb2_grpc


LOGGER = logging.getLogger(__name__)

MOCK_TENSOR_DATA = [0.104, 0.105]
MOCK_TENSOR_SHAPE = [2]
MOCK_TARGET_NEXT_LAYER = 1


def build_mock_payloads() -> Iterable[ldp_service_pb2.ActivationPayload]:
    yield ldp_service_pb2.ActivationPayload(
        token_index=0,
        tensor_data=MOCK_TENSOR_DATA,
        tensor_shape=MOCK_TENSOR_SHAPE,
        target_next_layer=MOCK_TARGET_NEXT_LAYER,
    )


def transmit_mock_activation() -> ldp_service_pb2.ForwardResponse:
    settings = get_settings()
    payloads = list(build_mock_payloads())
    LOGGER.info(
        "Connecting to worker at %s to send %s activation payload(s)",
        settings.transmitter_target,
        len(payloads),
    )

    with grpc.insecure_channel(settings.transmitter_target) as channel:
        stub = ldp_service_pb2_grpc.LLMPipelineServiceStub(channel)
        response = stub.ForwardActivationStream(iter(payloads))

    LOGGER.info(
        "Receiver response status_success=%s error_message=%r",
        response.status_success,
        response.error_message,
    )
    return response


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    transmit_mock_activation()
