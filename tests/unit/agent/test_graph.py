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
        """测试AsyncRedisSaver初始化成功（使用redis_url）"""
        # Mock settings使用redis模式
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "redis"
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_password = ""
        mock_settings.redis_db = 0

        # Mock AsyncRedisSaver
        mock_async_redis_saver_class = mocker.patch("langgraph.checkpoint.redis.aio.AsyncRedisSaver")
        mock_async_redis_saver_instance = MagicMock()
        mock_async_redis_saver_class.return_value = mock_async_redis_saver_instance

        # Import and compile
        from src.agent.main.graph import compile_agent_graph

        app = compile_agent_graph()

        # Verify AsyncRedisSaver created with redis_url (构造函数的第一个参数)
        mock_async_redis_saver_class.assert_called_once_with(
            "redis://localhost:6379/0"
        )

        # Verify app created successfully
        assert app is not None

    @pytest.mark.asyncio
    async def test_redis_checkpointer_fallback_on_import_error(self, mocker):
        """测试langgraph-checkpoint-redis未安装时降级到MemorySaver"""
        # Mock settings使用redis模式
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "redis"

        # Mock AsyncRedisSaver import失败
        def mock_import_error(*args, **kwargs):
            raise ImportError("langgraph-checkpoint-redis not installed")

        mocker.patch(
            "langgraph.checkpoint.redis.aio.AsyncRedisSaver",
            side_effect=mock_import_error,
        )

        # Import and compile (应该降级到MemorySaver)
        from src.agent.main.graph import compile_agent_graph

        app = compile_agent_graph()

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

        # Mock AsyncRedisSaver初始化失败
        mock_async_redis_saver_class = mocker.patch("langgraph.checkpoint.redis.aio.AsyncRedisSaver")
        mock_async_redis_saver_class.side_effect = RuntimeError(
            "Failed to connect to Redis"
        )

        # Import and compile (应该降级到MemorySaver)
        from src.agent.main.graph import compile_agent_graph

        app = compile_agent_graph()

        # Verify app still created (使用MemorySaver降级)
        assert app is not None

    @pytest.mark.asyncio
    async def test_unknown_checkpointer_fallback(self, mocker):
        """测试未知checkpointer类型时降级到MemorySaver"""
        # Mock settings使用未知类型
        mock_settings = mocker.patch("src.agent.main.graph.settings")
        mock_settings.langgraph_checkpointer = "unknown_type"

        # Import and compile
        from src.agent.main.graph import compile_agent_graph

        app = compile_agent_graph()

        # Verify app created (使用MemorySaver)
        assert app is not None

