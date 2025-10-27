"""
自动会话管理器单元测试

测试会话管理器的核心功能：
- 创建新会话
- 复用现有会话
- 用户 ID 优先
- Redis 失败降级
"""

import hashlib
from unittest.mock import AsyncMock, patch

import pytest

from src.core.session_manager import (
    SessionManager,
    get_or_create_session,
    get_session_manager,
)


@pytest.fixture
def session_manager():
    """创建会话管理器实例"""
    return SessionManager()


@pytest.fixture
def mock_redis():
    """模拟 Redis 客户端"""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.expire = AsyncMock(return_value=True)
    mock.aclose = AsyncMock()
    return mock


class TestSessionManager:
    """SessionManager 单元测试"""

    def test_build_redis_url_without_password(self, session_manager):
        """测试构建 Redis URL（无密码）"""
        with patch("src.core.session_manager.settings") as mock_settings:
            mock_settings.redis_password = ""
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.redis_db = 0

            url = session_manager._build_redis_url()
            assert url == "redis://localhost:6379/0"

    def test_build_redis_url_with_password(self, session_manager):
        """测试构建 Redis URL（有密码）"""
        with patch("src.core.session_manager.settings") as mock_settings:
            mock_settings.redis_password = "secret123"
            mock_settings.redis_host = "redis.example.com"
            mock_settings.redis_port = 6380
            mock_settings.redis_db = 1

            url = session_manager._build_redis_url()
            assert url == "redis://:secret123@redis.example.com:6380/1"

    def test_generate_client_fingerprint_with_user_id(self, session_manager):
        """测试生成客户端指纹（有 user_id）"""
        fingerprint = session_manager._generate_client_fingerprint(
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0",
            user_id="user123"
        )

        # 应该使用 user_id 作为指纹
        assert fingerprint == "user:user123"

    def test_generate_client_fingerprint_without_user_id(self, session_manager):
        """测试生成客户端指纹（无 user_id）"""
        client_ip = "192.168.1.100"
        user_agent = "Mozilla/5.0"

        fingerprint = session_manager._generate_client_fingerprint(
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=None
        )

        # 应该使用 IP + User-Agent 的 MD5 哈希
        expected_hash = hashlib.md5(f"{client_ip}|{user_agent}".encode()).hexdigest()
        assert fingerprint == f"client:{expected_hash}"

    def test_generate_session_id(self, session_manager):
        """测试生成 session_id"""
        session_id = session_manager._generate_session_id()

        # 应该以 "session-" 开头
        assert session_id.startswith("session-")
        # 应该有 12 个字符的十六进制后缀
        assert len(session_id) == len("session-") + 12

    @pytest.mark.asyncio
    async def test_get_or_create_session_new(self, session_manager, mock_redis):
        """测试创建新会话"""
        with patch.object(session_manager, "_get_redis_client", return_value=mock_redis):
            # Redis 返回 None（不存在）
            mock_redis.get = AsyncMock(return_value=None)

            session_id = await session_manager.get_or_create_session(
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0",
                user_id=None
            )

            # 应该创建新的 session_id
            assert session_id.startswith("session-")
            # 应该调用 Redis setex
            assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_get_or_create_session_reuse(self, session_manager, mock_redis):
        """测试复用现有会话"""
        existing_session_id = "session-abc123"

        with patch.object(session_manager, "_get_redis_client", return_value=mock_redis):
            # Redis 返回现有 session_id
            mock_redis.get = AsyncMock(return_value=existing_session_id)

            session_id = await session_manager.get_or_create_session(
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0",
                user_id=None
            )

            # 应该返回现有 session_id
            assert session_id == existing_session_id
            # 应该刷新过期时间
            assert mock_redis.expire.called

    @pytest.mark.asyncio
    async def test_get_or_create_session_with_user_id(self, session_manager, mock_redis):
        """测试使用 user_id 创建会话"""
        with patch.object(session_manager, "_get_redis_client", return_value=mock_redis):
            mock_redis.get = AsyncMock(return_value=None)

            session_id = await session_manager.get_or_create_session(
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0",
                user_id="user123"
            )

            # 应该创建新会话
            assert session_id.startswith("session-")
            # Redis key 应该包含 user:user123
            call_args = mock_redis.setex.call_args[0]
            assert "user:user123" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_or_create_session_redis_failure(self, session_manager):
        """测试 Redis 失败降级"""
        with patch.object(
            session_manager,
            "_get_redis_client",
            side_effect=Exception("Redis connection failed")
        ):
            session_id = await session_manager.get_or_create_session(
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0",
                user_id=None
            )

            # 应该回退到生成新 session_id
            assert session_id.startswith("session-")

    @pytest.mark.asyncio
    async def test_get_or_create_session_custom_timeout(self, session_manager, mock_redis):
        """测试自定义超时时间"""
        with patch.object(session_manager, "_get_redis_client", return_value=mock_redis):
            mock_redis.get = AsyncMock(return_value=None)

            await session_manager.get_or_create_session(
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0",
                user_id=None,
                timeout_minutes=60  # 自定义 60 分钟
            )

            # 应该使用 60 * 60 = 3600 秒
            call_args = mock_redis.setex.call_args[0]
            assert call_args[1] == 3600

    @pytest.mark.asyncio
    async def test_close_redis_connection(self, session_manager, mock_redis):
        """测试关闭 Redis 连接"""
        session_manager._redis_client = mock_redis

        await session_manager.close()

        # 应该调用 aclose
        assert mock_redis.aclose.called
        # 应该清空客户端引用
        assert session_manager._redis_client is None


class TestModuleFunctions:
    """模块级函数测试"""

    def test_get_session_manager_singleton(self):
        """测试单例模式"""
        manager1 = get_session_manager()
        manager2 = get_session_manager()

        # 应该返回同一个实例
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_or_create_session_convenience_function(self):
        """测试便捷函数"""
        with patch("src.core.session_manager.get_session_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.get_or_create_session = AsyncMock(return_value="session-test123")
            mock_get_manager.return_value = mock_manager

            session_id = await get_or_create_session(
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0"
            )

            # 应该调用管理器的方法
            assert mock_manager.get_or_create_session.called
            assert session_id == "session-test123"

