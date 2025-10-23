"""
LangGraph应用构建和配置的单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLangGraphCheckpointerInitialization:
    """测试LangGraph checkpointer初始化逻辑"""

    @pytest.mark.asyncio
    async def test_memory_checkpointer_initialization(self, mocker):
        """测试MemorySaver初始化成功"""
        # Mock settings使用memory模式
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "memory"

        # Import and compile
        from src.agent.main.graph import compile_agent_graph

        app = compile_agent_graph()

        # Verify app created successfully
        assert app is not None

    @pytest.mark.asyncio
    async def test_redis_checkpointer_initialization_success(self, mocker):
        """测试AsyncRedisSaver初始化成功"""
        # Mock settings使用redis模式
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "redis"
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_password = ""
        mock_settings.redis_db = 0

        # Mock redis.asyncio.Redis
        mock_redis_module = mocker.patch("redis.asyncio")
        mock_redis_instance = MagicMock()
        mock_redis_module.Redis.return_value = mock_redis_instance

        # Mock AsyncRedisSaver
        mock_async_redis_saver_class = mocker.patch("langgraph.checkpoint.redis.aio.AsyncRedisSaver")
        mock_async_redis_saver_instance = MagicMock()
        mock_async_redis_saver_class.return_value = mock_async_redis_saver_instance

        # Import and compile
        from src.agent.main.graph import compile_agent_graph

        app = compile_agent_graph()

        # Verify AsyncRedisSaver created with async redis client
        mock_async_redis_saver_class.assert_called_once_with(
            mock_redis_instance
        )

        # Verify app created successfully
        assert app is not None

    @pytest.mark.asyncio
    async def test_redis_checkpointer_fallback_on_import_error(self, mocker):
        """测试langgraph-checkpoint-redis未安装时降级到MemorySaver"""
        # Mock settings使用redis模式
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "redis"

        # Mock redis import成功，但AsyncRedisSaver import失败
        mocker.patch("src.agent.main.graph.redis.Redis")

        def mock_import_error(*args, **kwargs):
            raise ImportError("langgraph-checkpoint-redis not installed")

        mocker.patch(
            "src.agent.main.graph.AsyncRedisSaver",
            side_effect=mock_import_error,
        )

        # Import and build (应该降级到MemorySaver)
        from src.agent.main.graph import build_langgraph_app

        app = build_langgraph_app()

        # Verify app still created (使用MemorySaver)
        assert app is not None

    @pytest.mark.asyncio
    async def test_redis_checkpointer_fallback_on_runtime_error(self, mocker):
        """测试AsyncRedisSaver初始化失败时降级到MemorySaver"""
        # Mock settings使用redis模式
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "redis"
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_password = ""
        mock_settings.redis_db = 0

        # Mock 异步Redis客户端初始化成功
        mock_redis_class = mocker.patch("src.agent.main.graph.redis.Redis")
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance

        # Mock AsyncRedisSaver初始化失败
        mock_async_redis_saver_class = mocker.patch("src.agent.main.graph.AsyncRedisSaver")
        mock_async_redis_saver_class.side_effect = RuntimeError(
            "Failed to connect to Redis"
        )

        # Import and build (应该降级到MemorySaver)
        from src.agent.main.graph import build_langgraph_app

        app = build_langgraph_app()

        # Verify app still created (使用MemorySaver降级)
        assert app is not None

    @pytest.mark.asyncio
    async def test_unknown_checkpointer_fallback(self, mocker):
        """测试未知checkpointer类型时降级到MemorySaver"""
        # Mock settings使用未知类型
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "unknown_type"

        # Import and build
        from src.agent.main.graph import build_langgraph_app

        app = build_langgraph_app()

        # Verify app created (使用MemorySaver)
        assert app is not None

