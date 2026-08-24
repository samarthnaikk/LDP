"""Thread-safe payload queue for asynchronously decoupling network reception."""

from __future__ import annotations

from queue import Empty, Queue
from typing import Any


activation_queue: Queue[Any] = Queue()


def enqueue_payload(payload: Any) -> None:
    """Push a payload into the shared in-memory queue without blocking."""
    activation_queue.put_nowait(payload)


def get_queue() -> Queue[Any]:
    return activation_queue


def clear_queue() -> None:
    while True:
        try:
            activation_queue.get_nowait()
            activation_queue.task_done()
        except Empty:
            break
