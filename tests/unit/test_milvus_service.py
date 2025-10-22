"""
测试 Milvus 服务模块

测试 Milvus 向量数据库的连接、检索和插入逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.milvus_service import MilvusService


@pytest.mark.asyncio
async def test_milvus_initialize():
    """测试 Milvus 初始化"""
    service = MilvusService()

    with patch("src.services.milvus_service.AsyncMilvusClient") as mock_client_class:
        with patch.object(
            service, "_create_knowledge_collection", new_callable=AsyncMock
        ) as mock_create_knowledge:
            with patch.object(
                service, "_create_history_collection", new_callable=AsyncMock
            ) as mock_create_history:
                await service.initialize()

                mock_client_class.assert_called_once()
                # 应该初始化两个 collection（knowledge_base 和 conversation_history）
                mock_create_knowledge.assert_called_once()
                mock_create_history.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_close():
    """测试 Milvus 关闭连接"""
    service = MilvusService()
    
    # Mock client
    mock_client = AsyncMock()
    service.client = mock_client
    
    await service.close()
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_search_success(mock_embeddings):
    """测试向量检索成功"""
    service = MilvusService()
    
    # Mock AsyncMilvusClient
    mock_client = AsyncMock()
    service.client = mock_client

    # Mock 搜索结果 - AsyncMilvusClient返回字典格式
    mock_hit_1 = {
        "distance": 0.9,
        "entity": {
            "text": "文档1",
            "metadata": {"source": "doc1.md"},
        }
    }

    mock_hit_2 = {
        "distance": 0.8,
        "entity": {
            "text": "文档2",
            "metadata": {"source": "doc2.md"},
        }
    }

    mock_result = [[mock_hit_1, mock_hit_2]]
    mock_client.search.return_value = mock_result

    # 使用 query_embedding 参数
    query_embedding = [0.1] * 768
    results = await service.search_knowledge(query_embedding=query_embedding, top_k=2)

    assert len(results) <= 2
    mock_client.search.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_search_empty_query():
    """测试空向量"""
    service = MilvusService()
    
    # Mock client
    mock_client = AsyncMock()
    service.client = mock_client

    # 空的 embedding 向量会在 Milvus 搜索时触发错误
    # 这里测试传入空列表
    empty_embedding = []

    # Mock search to raise an error for empty embedding
    mock_client.search.side_effect = ValueError("Invalid embedding")

    with pytest.raises(ValueError):
        await service.search_knowledge(query_embedding=empty_embedding, top_k=3)


@pytest.mark.asyncio
async def test_milvus_insert_documents_success(mock_embeddings):
    """测试插入文档成功"""
    service = MilvusService()
    
    # Mock client
    mock_client = AsyncMock()
    service.client = mock_client

    documents = [
        {
            "id": "doc1",
            "text": "文档1",
            "embedding": [0.1] * 768,
            "metadata": {"source": "doc1.md"},
        },
        {
            "id": "doc2",
            "text": "文档2",
            "embedding": [0.2] * 768,
            "metadata": {"source": "doc2.md"},
        },
    ]

    # insert_knowledge 返回插入的数量
    result = await service.insert_knowledge(documents=documents)

    assert result == 2
    mock_client.insert.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_insert_empty_documents():
    """测试插入空文档列表"""
    service = MilvusService()
    
    # Mock client
    mock_client = AsyncMock()
    service.client = mock_client

    result = await service.insert_knowledge(documents=[])

    assert result == 0


@pytest.mark.asyncio
async def test_milvus_health_check_healthy():
    """测试健康检查 - 健康状态"""
    service = MilvusService()
    
    # Mock client已初始化
    mock_client = AsyncMock()
    service.client = mock_client

    is_healthy = service.health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_milvus_health_check_unhealthy():
    """测试健康检查 - 不健康状态"""
    service = MilvusService()

    with patch("pymilvus.connections.has_connection", return_value=False):
        is_healthy = service.health_check()
        assert is_healthy is False


@pytest.mark.asyncio
async def test_milvus_search_with_score_threshold(mock_embeddings):
    """测试带相似度阈值的检索"""
    service = MilvusService()
    
    # Mock client
    mock_client = AsyncMock()
    service.client = mock_client

    # Mock 搜索结果，包含不同COSINE距离值（越小越相似）
    mock_hit_high = {
        "distance": 0.1,  # COSINE距离：0.1（很相似，转换为相似度=0.95）
        "entity": {
            "text": "高相关文档",
            "metadata": {},
        }
    }

    mock_hit_low = {
        "distance": 1.0,  # COSINE距离：1.0（不太相似，转换为相似度=0.5）
        "entity": {
            "text": "低相关文档",
            "metadata": {},
        }
    }

    mock_result = [[mock_hit_high, mock_hit_low]]
    mock_client.search.return_value = mock_result

    query_embedding = [0.1] * 768
    # 设置较高的阈值，应该过滤掉低分文档
    results = await service.search_knowledge(
        query_embedding=query_embedding, top_k=10, score_threshold=0.8
    )

    # 结果应该被过滤，只保留高分文档
    assert isinstance(results, list)
    assert len(results) == 1
    # 距离0.1转换为相似度 = 1.0 - (0.1/2.0) = 0.95
    assert results[0]["score"] == 0.95


def test_milvus_singleton():
    """测试 Milvus Service 是单例"""
    from src.services.milvus_service import milvus_service as service1
    from src.services.milvus_service import milvus_service as service2

    assert service1 is service2


@pytest.mark.asyncio
async def test_milvus_search_score_is_similarity_not_distance():
    """测试返回的 score 是相似度而非距离（Issue #30 修复验证）"""
    service = MilvusService()
    
    # Mock client
    mock_client = AsyncMock()
    service.client = mock_client

    # Mock 搜索结果：COSINE距离值（越小越相似）
    mock_hit_1 = {
        "distance": 0.2,  # COSINE距离：0.2（很相似）
        "entity": {
            "text": "相似文档1",
            "metadata": {"source": "doc1.md"},
        }
    }

    mock_hit_2 = {
        "distance": 1.5,  # COSINE距离：1.5（不太相似）
        "entity": {
            "text": "不太相似文档2",
            "metadata": {"source": "doc2.md"},
        }
    }

    mock_result = [[mock_hit_1, mock_hit_2]]
    mock_client.search.return_value = mock_result

    query_embedding = [0.1] * 768
    results = await service.search_knowledge(query_embedding=query_embedding, top_k=2)

    # 验证返回的 score 是相似度（0-1范围，越大越相似）
    # 注意：第二个结果可能被阈值过滤掉，因为相似度0.25 < 默认阈值0.7
    assert len(results) >= 1  # 至少有一个结果

    # 第一个结果：距离0.2 -> 相似度 = 1.0 - (0.2/2.0) = 0.9
    assert results[0]["score"] == 0.9
    assert 0 <= results[0]["score"] <= 1  # 相似度在[0,1]范围内

    # 如果第二个结果通过了阈值过滤，验证其相似度
    if len(results) > 1:
        # 第二个结果：距离1.5 -> 相似度 = 1.0 - (1.5/2.0) = 0.25
        assert results[1]["score"] == 0.25
        assert 0 <= results[1]["score"] <= 1  # 相似度在[0,1]范围内

        # 验证相似度语义：第一个结果比第二个更相似
        assert results[0]["score"] > results[1]["score"]

