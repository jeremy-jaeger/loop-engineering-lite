#!/usr/bin/env bash
# Idempotent Cloud Agent setup for loop-engineering-lite.
# Prepares the local Ollama inference server, its model, and the test runner
# the harness shells out to. Safe to run repeatedly.
set -euo pipefail

MODEL="qwen3.5:0.8b"

# zstd is required to extract the Ollama release archive.
if ! command -v zstd >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq zstd
fi

# Ollama: the local LLM server the harness talks to at http://localhost:11434.
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# pytest: invoked as `python3 -m pytest` inside the VFS command simulation.
python3 -m pip install --user --break-system-packages --quiet pytest

# Pull the model the harness uses. It lives under ~/.ollama and is captured by
# the environment snapshot, so this is a no-op on subsequent boots.
if ! ollama list 2>/dev/null | grep -q "^${MODEL}"; then
  ollama serve >/tmp/ollama-install.log 2>&1 &
  OLLAMA_PID=$!
  for _ in $(seq 1 60); do
    if curl -sf http://localhost:11434/api/version >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  ollama pull "$MODEL"
  kill "$OLLAMA_PID" 2>/dev/null || true
  wait "$OLLAMA_PID" 2>/dev/null || true
fi

echo "loop-engineering-lite environment ready."
