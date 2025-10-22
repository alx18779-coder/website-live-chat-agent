"""Async Redis helper used by API endpoints."""

from __future__ import annotations

import logging
import time

from redis.asyncio import Redis

from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Thin wrapper around a Redis asyncio client."""

    def __init__(self) -> None:
        self._client: Redis | None = None

    async def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password or None,
                db=settings.redis_db,
                socket_timeout=1.0,
                socket_connect_timeout=0.5,
                decode_responses=True,
            )
        return self._client

    async def ping(self) -> tuple[bool, float | None]:
        """Ping Redis and return health together with latency (ms)."""

        start = time.perf_counter()
        try:
            client = await self._get_client()
            result = await client.ping()  # type: ignore[call-arg]
            latency = (time.perf_counter() - start) * 1000
            if result:
                return True, latency
            return False, latency
        except Exception as exc:  # noqa: BLE001 - we want to log the original error
            logger.warning("Redis ping failed: %s", exc)
            return False, None

    async def close(self) -> None:
        """Close the underlying Redis connection."""

        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception as exc:  # noqa: BLE001 - avoid masking shutdown issues
                logger.debug("Ignoring Redis close error: %s", exc)
            finally:
                self._client = None


redis_service = RedisService()

