# LLM Direct Protocol (LDP)

This repository contains a transport-layer MVP for the LLM Direct Protocol. The implementation lives under [`ldp-node/`](./ldp-node) and focuses only on point-to-point delivery of a mock activation payload from a Master node to a Worker node.

## What It Does

- uses gRPC over HTTP/2 for a persistent streaming connection
- uses Protocol Buffers for binary serialization
- receives payloads asynchronously and places them onto a thread-safe queue
- supports local execution and Docker Compose orchestration

## Project Layout

- [`ldp-node/proto/ldp_service.proto`](./ldp-node/proto/ldp_service.proto): gRPC service and message contract
- [`ldp-node/src/network/receiver.py`](./ldp-node/src/network/receiver.py): Worker-side gRPC receiver
- [`ldp-node/src/network/transmitter.py`](./ldp-node/src/network/transmitter.py): Master-side transmitter
- [`ldp-node/src/network/queue.py`](./ldp-node/src/network/queue.py): shared in-memory queue
- [`ldp-node/docker-compose.yml`](./ldp-node/docker-compose.yml): two-container demo

## Quick Start

```bash
cd ldp-node
python3.11 -m venv .venv
./.venv/bin/pip install -r requirements.txt
PYTHON_BIN=./.venv/bin/python ./scripts/compile_proto.sh
```

Start the receiver:

```bash
cd ldp-node
PYTHONPATH=src ./.venv/bin/python src/node.py receiver
```

In another terminal, send the mock payload:

```bash
cd ldp-node
PYTHONPATH=src ./.venv/bin/python src/node.py transmitter
```

## Full Usage Docs

- Repo-level overview: [`ldp-node/README.md`](./ldp-node/README.md)
- Step-by-step usage guide: [`ldp-node/docs/USAGE.md`](./ldp-node/docs/USAGE.md)

## Verification

Run the test suite with:

```bash
cd ldp-node
PYTHONPATH=src ./.venv/bin/pytest
```
