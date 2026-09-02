#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-"$ROOT_DIR/.venv311/bin/python"}"
PORT="${LDP_SMOKE_PORT:-50071}"
LOG_DIR="${LDP_LOG_DIR:-"$ROOT_DIR/logs/smoke"}"
RECEIVER_HOST="${LDP_RECEIVER_HOST:-0.0.0.0}"
TRANSMITTER_HOST="${LDP_TRANSMITTER_HOST:-127.0.0.1}"

mkdir -p "$LOG_DIR"
rm -f "$LOG_DIR/receiver.log" "$LOG_DIR/transmitter.log"

cleanup() {
  if [[ -n "${RECEIVER_PID:-}" ]] && kill -0 "$RECEIVER_PID" 2>/dev/null; then
    kill "$RECEIVER_PID" 2>/dev/null || true
    wait "$RECEIVER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

pushd "$ROOT_DIR" >/dev/null

PYTHONPATH=src \
LDP_LOG_DIR="$LOG_DIR" \
LDP_RECEIVER_HOST="$RECEIVER_HOST" \
LDP_RECEIVER_PORT="$PORT" \
"$PYTHON_BIN" src/receive.py >"$LOG_DIR/receiver.stdout.log" 2>&1 &
RECEIVER_PID=$!

sleep 1

PYTHONPATH=src \
LDP_LOG_DIR="$LOG_DIR" \
LDP_TRANSMITTER_HOST="$TRANSMITTER_HOST" \
LDP_TRANSMITTER_PORT="$PORT" \
"$PYTHON_BIN" src/transmit.py >"$LOG_DIR/transmitter.stdout.log" 2>&1

grep -q "Receiver listening on ${RECEIVER_HOST}:${PORT}" "$LOG_DIR/receiver.log"
grep -q "Queued activation payload token_index=0 target_next_layer=1" "$LOG_DIR/receiver.log"
grep -q "status_success=True" "$LOG_DIR/transmitter.log"

echo "Smoke test passed. Logs written to $LOG_DIR"

popd >/dev/null
