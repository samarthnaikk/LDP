"""Dedicated entrypoint for running the LDP transmitter."""

from __future__ import annotations

from logging_utils import configure_logging
from network.transmitter import transmit_mock_activation


def main() -> None:
    configure_logging("transmitter")
    transmit_mock_activation()


if __name__ == "__main__":
    main()
