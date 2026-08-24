#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_DIR="${ROOT_DIR}/proto"
OUT_DIR="${ROOT_DIR}/src/generated"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"${PYTHON_BIN}" -m grpc_tools.protoc \
  -I "${PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTO_DIR}/ldp_service.proto"

ROOT_DIR="${ROOT_DIR}" "${PYTHON_BIN}" - <<'PY'
import os
from pathlib import Path

grpc_file = Path(os.environ["ROOT_DIR"]) / "src/generated/ldp_service_pb2_grpc.py"
contents = grpc_file.read_text()
contents = contents.replace(
    "import ldp_service_pb2 as ldp__service__pb2",
    "from generated import ldp_service_pb2 as ldp__service__pb2",
)
grpc_file.write_text(contents)
PY
