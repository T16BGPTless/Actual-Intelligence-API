#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to read local Supabase env." >&2
  exit 1
fi

echo "[run_local] Reading Supabase local env..."
eval "$(npx --yes supabase status -o env)"

export SUPABASE_URL="${API_URL:-}"
export SUPABASE_ANON_KEY="${ANON_KEY:-}"
export SUPABASE_SERVICE_ROLE_KEY="${SERVICE_ROLE_KEY:-}"
export PYTHONPATH="$ROOT_DIR"
PORT="${BACKEND_PORT:-5001}"

if [[ -z "${SUPABASE_URL}" || -z "${SUPABASE_ANON_KEY}" || -z "${SUPABASE_SERVICE_ROLE_KEY}" ]]; then
  echo "Missing Supabase env vars. Is local Supabase running? Try: npx supabase start" >&2
  exit 1
fi

while lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

echo "[run_local] Starting Flask API on http://127.0.0.1:${PORT}"
exec ../venv/bin/python -c "from app.app import app; app.run(debug=True, host='127.0.0.1', port=${PORT})"
