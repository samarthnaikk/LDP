"""Dedicated entrypoint for running the LDP transmitter."""

from __future__ import annotations

import logging

from network.transmitter import transmit_mock_activation


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    transmit_mock_activation()


if __name__ == "__main__":
    main()
