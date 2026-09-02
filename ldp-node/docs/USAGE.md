# LDP Node Usage Guide

This guide explains how to build, run, and verify the LDP transport MVP in `ldp-node/`.

## Overview

The transport flow is:

1. The Worker starts a gRPC server.
2. The Master opens a gRPC channel to the Worker.
3. The Master streams a mock `ActivationPayload`.
4. The Worker pushes each payload into an in-memory thread-safe queue.
5. The Worker returns a `ForwardResponse` confirming success.

## Prerequisites

- Python 3.11 or newer
- `pip`
- Docker and Docker Compose if you want the containerized demo

## Setup

From the repo root:

```bash
cd ldp-node
python3.11 -m venv .venv
./.venv/bin/pip install -r requirements.txt
PYTHON_BIN=./.venv/bin/python ./scripts/compile_proto.sh
```

What this does:

- creates a local virtual environment
- installs gRPC, grpc-tools, and the test dependencies
- generates Python gRPC modules into `src/generated/`

## Configuration

The runtime is controlled by environment variables in `src/config/settings.py`.

Defaults:

- `LDP_RECEIVER_HOST=0.0.0.0`
- `LDP_RECEIVER_PORT=50051`
- `LDP_TRANSMITTER_HOST=127.0.0.1`
- `LDP_TRANSMITTER_PORT=50051`

Typical local override example:

```bash
export LDP_RECEIVER_PORT=50052
export LDP_TRANSMITTER_PORT=50052
```

## Running Locally

Start the Worker receiver in one terminal:

```bash
cd ldp-node
PYTHONPATH=src ./.venv/bin/python src/receive.py
```

Expected behavior:

- the gRPC server binds to the configured receiver address
- each incoming payload is logged and queued

Start the Master transmitter in a second terminal:

```bash
cd ldp-node
PYTHONPATH=src ./.venv/bin/python src/transmit.py
```

Expected behavior:

- the transmitter connects to the configured Worker target
- it sends a deterministic mock payload representing a tiny activation tensor
- it logs the `status_success` response from the Worker

If you need the older single-file wrapper, `src/node.py` still supports:

```bash
PYTHONPATH=src ./.venv/bin/python src/node.py receiver
PYTHONPATH=src ./.venv/bin/python src/node.py transmitter
```

## Running with Docker Compose

From `ldp-node/`:

```bash
docker compose up --build
```

What happens:

- `worker` starts first and listens on port `50051`
- `master` waits briefly, then connects to `worker:50051`
- the payload is transmitted over the internal Compose network

To stop the stack:

```bash
docker compose down
```

## Testing

Run all tests:

```bash
cd ldp-node
PYTHONPATH=src ./.venv/bin/pytest
```

The suite covers:

- receiver behavior and response handling
- high-frequency queue drops using `pytest-timeout`
- a live gRPC integration test when the environment allows local socket binding

## Troubleshooting

If proto imports fail:

```bash
PYTHON_BIN=./.venv/bin/python ./scripts/compile_proto.sh
```

If the transmitter cannot connect:

- confirm the receiver is already running
- confirm `LDP_TRANSMITTER_HOST` and `LDP_TRANSMITTER_PORT` match the receiver
- check that the selected port is not already in use

If Docker Compose does not pass the payload:

- rebuild with `docker compose up --build`
- inspect service logs with `docker compose logs worker` and `docker compose logs master`
