# LDP Transport MVP

This project contains a Python and gRPC Minimum Viable Product for the LLM Direct Protocol transport layer. It streams a mock activation payload one-way from a master node to a worker node over HTTP/2, serializes payloads with Protocol Buffers, and decouples network reception from execution with a thread-safe queue.

For a step-by-step runbook, see [`docs/USAGE.md`](./docs/USAGE.md).

## Directory Layout

```text
ldp-node/
├── proto/
│   └── ldp_service.proto
├── scripts/
│   └── compile_proto.sh
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── generated/
│   │   ├── __init__.py
│   │   ├── ldp_service_pb2.py
│   │   └── ldp_service_pb2_grpc.py
│   ├── network/
│   │   ├── __init__.py
│   │   ├── queue.py
│   │   ├── receiver.py
│   │   └── transmitter.py
│   ├── __init__.py
│   └── node.py
├── tests/
│   ├── conftest.py
│   └── test_transport.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.11 or newer
- `pip`
- Docker and Docker Compose for the container workflow

## Install Dependencies

```bash
python3.11 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Compile Protocol Buffers

```bash
PYTHON_BIN=./.venv/bin/python ./scripts/compile_proto.sh
```

The script generates `ldp_service_pb2.py` and `ldp_service_pb2_grpc.py` in `src/generated/`.

## Local Runtime

Start the worker receiver:

```bash
PYTHONPATH=src ./.venv/bin/python src/node.py receiver
```

In a second terminal, send the mock activation stream from the master transmitter:

```bash
PYTHONPATH=src ./.venv/bin/python src/node.py transmitter
```

Environment variables:

- `LDP_RECEIVER_HOST` defaults to `0.0.0.0`
- `LDP_RECEIVER_PORT` defaults to `50051`
- `LDP_TRANSMITTER_HOST` defaults to `127.0.0.1`
- `LDP_TRANSMITTER_PORT` defaults to `50051`

## What You Should See

When the receiver is running and the transmitter sends the payload:

- the receiver logs that it queued an activation payload
- the transmitter logs `status_success=True`
- the stream completes with a positive `ForwardResponse`

## Tests

Run the queue and transport tests with:

```bash
PYTHONPATH=src ./.venv/bin/pytest
```

The suite includes:

- a receiver unit test that confirms payloads are queued and acknowledged
- a high-frequency queue stress test guarded by `pytest-timeout`
- a gRPC integration test that runs when the environment allows local socket binding

## Docker Compose

Build and run the worker and master services:

```bash
docker compose up --build
```

The `worker` service starts the receiver, and the `master` service waits briefly before transmitting the mock activation payload to `worker:50051` over the internal Compose network.
