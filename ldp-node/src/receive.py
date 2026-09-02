"""Dedicated entrypoint for running the LDP receiver."""

from __future__ import annotations

from logging_utils import configure_logging
from network.receiver import serve


def main() -> None:
    configure_logging("receiver")
    serve()


if __name__ == "__main__":
    main()
