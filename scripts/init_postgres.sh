#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "${ROOT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
  echo "[init_postgres] 错误: 需要安装 uv (https://github.com/astral-sh/uv)。" >&2
  exit 1
fi

if [ -f .env ]; then
  echo "[init_postgres] 载入 .env 中的数据库配置"
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
export POSTGRES_DATABASE="${POSTGRES_DATABASE:-chat_agent}"
export POSTGRES_POOL_SIZE="${POSTGRES_POOL_SIZE:-5}"
export POSTGRES_MAX_OVERFLOW="${POSTGRES_MAX_OVERFLOW:-5}"
export POSTGRES_ECHO="${POSTGRES_ECHO:-false}"

cat <<MSG
[init_postgres] 即将运行 Alembic 迁移：
  Host: ${POSTGRES_HOST}
  Port: ${POSTGRES_PORT}
  Database: ${POSTGRES_DATABASE}
  User: ${POSTGRES_USER}
MSG

uv run alembic upgrade head

echo "[init_postgres] ✅ PostgreSQL 迁移已应用"
