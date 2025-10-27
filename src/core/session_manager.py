"""
自动会话管理模块

为无状态客户端提供自动会话管理能力，支持：
- 客户端指纹识别（IP + User-Agent / User ID）
- Redis 映射存储和自动过期
- 错误隔离和降级处理

Author: LD
Created: 2025-10-27
Related Issue: #74
"""

import hashlib
import logging
import uuid
from typing import Optional

import redis.asyncio as redis

from src.core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器

    负责为无状态客户端分配和维护稳定的 session_id
    """

    def __init__(self):
        """初始化会话管理器"""
        self._redis_client: Optional[redis.Redis] = None
        self._redis_url = self._build_redis_url()

    def _build_redis_url(self) -> str:
        """
        构建 Redis 连接 URL

        Returns:
            Redis 连接 URL 字符串
        """
        redis_url = "redis://"
        if settings.redis_password:
            redis_url += f":{settings.redis_password}@"
        redis_url += f"{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        return redis_url

    async def _get_redis_client(self) -> redis.Redis:
        """
        获取 Redis 客户端（延迟初始化）

        Returns:
            Redis 客户端实例

        Raises:
            redis.RedisError: Redis 连接失败
        """
        if self._redis_client is None:
            try:
                self._redis_client = await redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=settings.redis_max_connections,
                )
                # 测试连接
                await self._redis_client.ping()
                logger.debug("✅ Redis 连接成功")
            except Exception as e:
                logger.error(f"❌ Redis 连接失败: {e}")
                raise

        return self._redis_client

    def _generate_client_fingerprint(
        self,
        client_ip: str,
        user_agent: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        生成客户端唯一指纹

        优先级：
        1. user_id（如果提供 X-User-ID Header）
        2. IP + User-Agent 的 MD5 哈希

        Args:
            client_ip: 客户端 IP 地址
            user_agent: User-Agent 字符串
            user_id: 可选的用户 ID（来自认证系统）

        Returns:
            客户端唯一指纹字符串
        """
        if user_id:
            # 优先使用 user_id（已认证用户）
            fingerprint = f"user:{user_id}"
            logger.debug(f"使用 user_id 生成指纹: {fingerprint}")
        else:
            # 使用 IP + User-Agent 生成哈希
            raw_fingerprint = f"{client_ip}|{user_agent}"
            fingerprint = f"client:{hashlib.md5(raw_fingerprint.encode()).hexdigest()}"
            logger.debug(f"使用 IP+UA 生成指纹: {fingerprint}")

        return fingerprint

    def _generate_session_id(self) -> str:
        """
        生成新的 session_id

        Returns:
            新的 session_id 字符串
        """
        return f"session-{uuid.uuid4().hex[:12]}"

    async def get_or_create_session(
        self,
        client_ip: str,
        user_agent: str,
        user_id: Optional[str] = None,
        timeout_minutes: int = 30
    ) -> str:
        """
        获取或创建会话

        逻辑流程：
        1. 生成客户端指纹（user_id 优先，否则 IP+User-Agent）
        2. 查询 Redis: session:mapping:{fingerprint}
        3. 如果找到 → 刷新过期时间并返回
        4. 如果未找到 → 创建新 session_id 并保存映射

        Args:
            client_ip: 客户端 IP 地址
            user_agent: User-Agent 字符串
            user_id: 可选的用户 ID（来自 X-User-ID Header）
            timeout_minutes: 会话超时时间（分钟），默认 30 分钟

        Returns:
            稳定的 session_id

        Note:
            如果 Redis 连接失败，会回退到生成新的 session_id
        """
        # 生成客户端指纹
        fingerprint = self._generate_client_fingerprint(client_ip, user_agent, user_id)
        redis_key = f"session:mapping:{fingerprint}"

        try:
            # 获取 Redis 客户端
            redis_client = await self._get_redis_client()

            # 查询现有 session_id
            existing_session_id = await redis_client.get(redis_key)

            if existing_session_id:
                # 找到现有会话，刷新过期时间
                await redis_client.expire(redis_key, timeout_minutes * 60)
                logger.info(
                    f"♻️ 复用现有会话 | fingerprint={fingerprint} | "
                    f"session_id={existing_session_id}"
                )
                return existing_session_id
            else:
                # 创建新会话
                new_session_id = self._generate_session_id()
                await redis_client.setex(
                    redis_key,
                    timeout_minutes * 60,
                    new_session_id
                )
                logger.info(
                    f"✨ 创建新会话 | fingerprint={fingerprint} | "
                    f"session_id={new_session_id} | timeout={timeout_minutes}min"
                )
                return new_session_id

        except Exception as e:
            # Redis 失败时回退到生成新 session_id
            fallback_session_id = self._generate_session_id()
            logger.error(
                f"❌ Redis 会话管理失败: {e}，回退到新 session_id: {fallback_session_id}",
                exc_info=True
            )
            return fallback_session_id

    async def close(self):
        """
        关闭 Redis 连接

        Note:
            应在应用关闭时调用，释放资源
        """
        if self._redis_client:
            try:
                await self._redis_client.aclose()
                logger.debug("✅ Redis 连接已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭 Redis 连接失败: {e}")
            finally:
                self._redis_client = None


# 全局单例实例
_session_manager_instance: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    获取会话管理器单例实例

    Returns:
        SessionManager 实例
    """
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance


async def get_or_create_session(
    client_ip: str,
    user_agent: str,
    user_id: Optional[str] = None,
    timeout_minutes: int = 30
) -> str:
    """
    便捷函数：获取或创建会话

    Args:
        client_ip: 客户端 IP 地址
        user_agent: User-Agent 字符串
        user_id: 可选的用户 ID（来自 X-User-ID Header）
        timeout_minutes: 会话超时时间（分钟），默认 30 分钟

    Returns:
        稳定的 session_id
    """
    manager = get_session_manager()
    return await manager.get_or_create_session(
        client_ip, user_agent, user_id, timeout_minutes
    )

