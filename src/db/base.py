"""
数据库基础层

提供 SQLAlchemy Base 类和数据库服务。
"""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 基础模型类"""
    pass


class DatabaseService:
    """数据库服务类，管理异步数据库连接"""

    def __init__(self, database_url: str):
        """
        初始化数据库服务

        Args:
            database_url: 数据库连接 URL
        """
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.async_session = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    @asynccontextmanager
    async def get_session(self):
        """
        获取异步数据库会话的上下文管理器

        Yields:
            AsyncSession: 异步数据库会话
        """
        async with self.async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()
