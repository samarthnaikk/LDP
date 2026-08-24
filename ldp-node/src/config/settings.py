"""Environment-driven runtime settings for the LDP transport MVP."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_RECEIVER_HOST = "0.0.0.0"
DEFAULT_RECEIVER_PORT = 50051
DEFAULT_TRANSMITTER_HOST = "127.0.0.1"
DEFAULT_TRANSMITTER_PORT = 50051


@dataclass(frozen=True)
class Settings:
    receiver_host: str = DEFAULT_RECEIVER_HOST
    receiver_port: int = DEFAULT_RECEIVER_PORT
    transmitter_host: str = DEFAULT_TRANSMITTER_HOST
    transmitter_port: int = DEFAULT_TRANSMITTER_PORT

    @property
    def receiver_address(self) -> str:
        return f"{self.receiver_host}:{self.receiver_port}"

    @property
    def transmitter_target(self) -> str:
        return f"{self.transmitter_host}:{self.transmitter_port}"


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {value!r}.") from exc


def get_settings() -> Settings:
    return Settings(
        receiver_host=os.getenv("LDP_RECEIVER_HOST", DEFAULT_RECEIVER_HOST),
        receiver_port=_read_int("LDP_RECEIVER_PORT", DEFAULT_RECEIVER_PORT),
        transmitter_host=os.getenv("LDP_TRANSMITTER_HOST", DEFAULT_TRANSMITTER_HOST),
        transmitter_port=_read_int("LDP_TRANSMITTER_PORT", DEFAULT_TRANSMITTER_PORT),
    )
