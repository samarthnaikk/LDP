"""Dedicated entrypoint for running the LDP receiver."""

from __future__ import annotations

import logging

from network.receiver import serve


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    serve()


if __name__ == "__main__":
    main()
