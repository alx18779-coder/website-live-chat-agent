"""
测试 Milvus 统计查询修复
"""

from unittest.mock import AsyncMock

import pytest

from src.repositories.milvus.knowledge_repository import KnowledgeRepository


class TestMilvusCountFix:
    """测试 Milvus 统计查询修复"""

    @pytest.fixture
    def mock_client(self):
        """模拟 Milvus 客户端"""
        client = AsyncMock()
        return client

    @pytest.fixture
    def repository(self, mock_client):
        """创建知识库仓库实例"""
        return KnowledgeRepository(client=mock_client)

    @pytest.mark.asyncio
    async def test_count_documents_correct_implementation(self, repository, mock_client):
        """测试 count_documents 方法的正确实现"""
        # 模拟 Milvus 查询返回（现在返回文档列表）
        mock_client.query.return_value = [
            {"id": "doc1"}, {"id": "doc2"}, {"id": "doc3"}  # 3个文档
        ]

        # 调用方法
        result = await repository.count_documents()

        # 验证结果
        assert result == 3

        # 验证查询参数
        mock_client.query.assert_called_once_with(
            collection_name="knowledge_base",
            filter="created_at > 0",
            output_fields=["id"],
            limit=16384
        )

    @pytest.mark.asyncio
    async def test_count_documents_empty_results(self, repository, mock_client):
        """测试空结果的情况"""
        # 模拟空结果
        mock_client.query.return_value = []

        # 调用方法
        result = await repository.count_documents()

        # 验证结果
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_documents_no_count_field(self, repository, mock_client):
        """测试结果中没有 id 字段的情况"""
        # 模拟没有 id 字段的结果
        mock_client.query.return_value = [{"other_field": "value"}]

        # 调用方法
        result = await repository.count_documents()

        # 验证结果（应该返回列表长度）
        assert result == 1

    @pytest.mark.asyncio
    async def test_count_documents_exception_handling(self, repository, mock_client):
        """测试异常处理"""
        # 模拟查询异常
        mock_client.query.side_effect = Exception("Milvus connection error")

        # 调用方法
        result = await repository.count_documents()

        # 验证结果（异常时应该返回 0）
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_documents_large_number(self, repository, mock_client):
        """测试大数字的情况"""
        # 模拟大量文档结果
        large_count = 1000
        mock_client.query.return_value = [{"id": f"doc{i}"} for i in range(large_count)]

        # 调用方法
        result = await repository.count_documents()

        # 验证结果
        assert result == large_count

    def test_count_documents_method_exists(self, repository):
        """测试 count_documents 方法存在"""
        assert hasattr(repository, 'count_documents')
        assert callable(getattr(repository, 'count_documents'))
