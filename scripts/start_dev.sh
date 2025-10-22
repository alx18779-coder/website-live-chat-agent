#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "${ROOT_DIR}"

if command -v uv >/dev/null 2>&1; then
  echo "[start_dev] Ensuring Python dependencies via uv sync..."
  uv sync
else
  echo "[start_dev] Error: uv is required (https://github.com/astral-sh/uv)." >&2
  exit 1
fi

if [ -f .env ]; then
  echo "[start_dev] Loading variables from .env"
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

export LANGGRAPH_CHECKPOINTER="${LANGGRAPH_CHECKPOINTER:-memory}"
export MILVUS_HOST="${MILVUS_HOST:-localhost}"
export MILVUS_PORT="${MILVUS_PORT:-19530}"
export MILVUS_USER="${MILVUS_USER:-root}"
export MILVUS_PASSWORD="${MILVUS_PASSWORD:-}"
export MILVUS_DATABASE="${MILVUS_DATABASE:-default}"
export API_KEY="${API_KEY:-dev-api-key}"
export LLM_PROVIDER="${LLM_PROVIDER:-deepseek}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-dev-placeholder}"
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-chat}"
export EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-deepseek}"
export DEEPSEEK_EMBEDDING_API_KEY="${DEEPSEEK_EMBEDDING_API_KEY:-dev-placeholder}"
export DEEPSEEK_EMBEDDING_MODEL="${DEEPSEEK_EMBEDDING_MODEL:-deepseek-embedding}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
export POSTGRES_DATABASE="${POSTGRES_DATABASE:-chat_agent}"
export POSTGRES_POOL_SIZE="${POSTGRES_POOL_SIZE:-5}"
export POSTGRES_MAX_OVERFLOW="${POSTGRES_MAX_OVERFLOW:-5}"
export POSTGRES_ECHO="${POSTGRES_ECHO:-false}"

PORT="${PORT:-8000}"

cat <<MSG
[start_dev] Launching FastAPI dev server with:
  - MILVUS_HOST=${MILVUS_HOST}
  - LANGGRAPH_CHECKPOINTER=${LANGGRAPH_CHECKPOINTER}
  - POSTGRES_HOST=${POSTGRES_HOST}
  - PORT=${PORT}
MSG

exec uv run uvicorn src.main:app --reload --host 0.0.0.0 --port "${PORT}"
