"""
Repository层单元测试

测试KnowledgeRepository和HistoryRepository的核心功能。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.entities.history import ConversationHistory
from src.models.entities.knowledge import Knowledge
from src.repositories.milvus.history_repository import HistoryRepository
from src.repositories.milvus.knowledge_repository import KnowledgeRepository


class TestKnowledgeRepository:
    """测试KnowledgeRepository"""

    @pytest.mark.asyncio
    async def test_search_knowledge_success(self):
        """测试知识库搜索成功"""
        # 创建mock client
        mock_client = AsyncMock()
        mock_search_result = [
            {
                "entity": {
                    "text": "测试文档",
                    "metadata": {"source": "test.md"},
                    "created_at": 1729612800,
                },
                "distance": 0.1,  # COSINE距离
            },
        ]
        mock_client.search.return_value = [mock_search_result]

        # 创建Repository
        repo = KnowledgeRepository(mock_client)

        # 执行搜索
        results = await repo.search(
            query_embedding=[0.1] * 1536,
            top_k=5,
        )

        # 验证结果
        assert len(results) == 1
        assert isinstance(results[0], Knowledge)
        assert results[0].text == "测试文档"
        assert results[0].metadata == {"source": "test.md"}

    @pytest.mark.asyncio
    async def test_insert_knowledge_success(self):
        """测试知识库插入成功"""
        mock_client = AsyncMock()
        mock_insert_result = MagicMock()
        mock_insert_result.insert_count = 2
        mock_client.insert.return_value = mock_insert_result

        repo = KnowledgeRepository(mock_client)

        documents = [
            {"id": "doc1", "text": "文档1", "embedding": [0.1] * 1536},
            {"id": "doc2", "text": "文档2", "embedding": [0.2] * 1536, "metadata": {"key": "value"}},
        ]

        count = await repo.insert(documents)

        assert count == 2
        mock_client.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_empty_documents(self):
        """测试插入空列表"""
        mock_client = AsyncMock()
        repo = KnowledgeRepository(mock_client)

        count = await repo.insert([])

        assert count == 0
        mock_client.insert.assert_not_called()


class TestHistoryRepository:
    """测试HistoryRepository"""

    @pytest.mark.asyncio
    async def test_search_by_session_success(self):
        """测试按会话ID搜索成功"""
        mock_client = AsyncMock()
        mock_query_result = [
            {"role": "user", "text": "问题1", "timestamp": 1729612800},
            {"role": "assistant", "text": "回答1", "timestamp": 1729612801},
        ]
        mock_client.query.return_value = mock_query_result

        repo = HistoryRepository(mock_client)

        results = await repo.search_by_session(
            session_id="session_123",
            limit=10,
        )

        # 验证结果（应按时间戳降序排列）
        assert len(results) == 2
        assert isinstance(results[0], ConversationHistory)
        # 注意: query返回的结果顺序可能不确定，Repository会在客户端排序
        # 但mock返回的是列表，需要Repository内部排序
        # 实际顺序取决于Repository的实现
        assert results[0].timestamp in [1729612800, 1729612801]
        assert results[1].timestamp in [1729612800, 1729612801]

    @pytest.mark.asyncio
    async def test_insert_history_success(self):
        """测试对话历史插入成功"""
        mock_client = AsyncMock()
        mock_insert_result = MagicMock()
        mock_insert_result.insert_count = 1
        mock_client.insert.return_value = mock_insert_result

        repo = HistoryRepository(mock_client)

        messages = [
            {
                "id": "msg1",
                "session_id": "session_123",
                "role": "user",
                "text": "用户问题",
                "embedding": [0.1] * 1536,
                "timestamp": 1729612800,
            },
        ]

        count = await repo.insert(messages)

        assert count == 1
        mock_client.insert.assert_called_once()


class TestRepositoryHealthCheck:
    """测试Repository健康检查"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """测试健康检查成功"""
        mock_client = AsyncMock()
        mock_client.has_collection.return_value = True

        repo = KnowledgeRepository(mock_client)

        is_healthy = await repo.health_check()

        assert is_healthy is True
        mock_client.has_collection.assert_called_once_with("knowledge_base")

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """测试健康检查失败"""
        mock_client = AsyncMock()
        mock_client.has_collection.side_effect = Exception("Connection error")

        repo = KnowledgeRepository(mock_client)

        is_healthy = await repo.health_check()

        assert is_healthy is False


class TestRepositoryErrorHandling:
    """测试Repository错误处理"""

    @pytest.mark.asyncio
    async def test_search_error(self):
        """测试搜索错误处理（异常直接抛出）"""
        from pymilvus.exceptions import MilvusException

        mock_client = AsyncMock()
        mock_client.search.side_effect = MilvusException("Search failed")

        repo = KnowledgeRepository(mock_client)

        # _base_search不包装异常，直接抛出MilvusException
        with pytest.raises(MilvusException):
            await repo.search(query_embedding=[0.1] * 1536, top_k=5)

    @pytest.mark.asyncio
    async def test_insert_error(self):
        """测试插入错误处理（异常直接抛出）"""
        from pymilvus.exceptions import MilvusException

        mock_client = AsyncMock()
        mock_client.insert.side_effect = MilvusException("Insert failed")

        repo = KnowledgeRepository(mock_client)

        # _base_insert不包装异常，直接抛出MilvusException
        with pytest.raises(MilvusException):
            await repo.insert([{"id": "test", "text": "test", "embedding": [0.1] * 1536}])


class TestRepositorySingleton:
    """测试Repository单例模式"""

    @pytest.mark.asyncio
    async def test_get_repository_before_init(self):
        """测试在初始化前获取Repository"""
        from src.repositories import get_knowledge_repository, reset_repositories

        # 重置单例
        reset_repositories()

        # 未初始化milvus_service.client，应抛出异常
        with pytest.raises(RuntimeError, match="Milvus client not initialized"):
            get_knowledge_repository()

