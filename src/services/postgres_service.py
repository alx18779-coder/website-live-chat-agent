"""PostgreSQL 异步连接服务"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.core.exceptions import PostgresConnectionError

logger = logging.getLogger(__name__)


class PostgresService:
    """管理 PostgreSQL 异步引擎与会话生命周期"""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def is_initialized(self) -> bool:
        """判断服务是否已初始化"""

        return self._engine is not None and self._session_factory is not None

    async def initialize(self) -> None:
        """初始化 PostgreSQL 连接"""

        if self.is_initialized:
            return

        try:
            self._engine = create_async_engine(
                settings.postgres_async_dsn,
                pool_size=settings.postgres_pool_size,
                max_overflow=settings.postgres_max_overflow,
                echo=settings.postgres_echo,
                pool_pre_ping=True,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
            )

            # 验证连接是否可用
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

            logger.info(
                "✅ Connected to PostgreSQL: %s:%s/%s",
                settings.postgres_host,
                settings.postgres_port,
                settings.postgres_database,
            )
        except Exception as exc:  # noqa: BLE001 - 捕获底层库异常并统一封装
            await self.close()
            logger.error("❌ Failed to initialize PostgreSQL: %s", exc)
            raise PostgresConnectionError(f"Failed to initialize PostgreSQL: {exc}") from exc

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """获取一个异步会话上下文"""

        if self._session_factory is None:
            raise PostgresConnectionError("PostgreSQL engine has not been initialised")

        session = self._session_factory()
        try:
            yield session
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """执行健康检查"""

        if self._engine is None:
            return False

        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as exc:
            logger.error("PostgreSQL health check failed: %s", exc)
            return False

    async def close(self) -> None:
        """关闭引擎并释放资源"""

        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._session_factory = None


postgres_service = PostgresService()
