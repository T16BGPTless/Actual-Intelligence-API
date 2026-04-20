#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d "../venv" ]; then
    echo "Virtual environment not found at ../venv."
    echo "Please create it and install requirements.txt first."
    exit 1
fi

source ../venv/bin/activate
export PYTHONPATH="$ROOT_DIR"

echo "[run_tests] Running pytest test suite..."
exec pytest "$@"
