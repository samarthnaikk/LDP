"""Thin entrypoint for running the LDP master or worker roles."""

from __future__ import annotations

import argparse

from network.receiver import serve as serve_receiver
from network.transmitter import transmit_mock_activation


def main() -> None:
    parser = argparse.ArgumentParser(description="LDP transport node entrypoint")
    parser.add_argument("role", choices=("receiver", "transmitter"))
    args = parser.parse_args()

    if args.role == "receiver":
        serve_receiver()
        return

    transmit_mock_activation()


if __name__ == "__main__":
    main()
