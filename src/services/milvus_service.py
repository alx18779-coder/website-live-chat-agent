"""
Milvus 向量数据库服务

⚠️ DEPRECATED: 此服务已废弃，请使用新的Repository模式。

提供知识库和对话历史的向量存储与检索功能。
使用AsyncMilvusClient实现原生异步操作，支持高并发场景。

迁移指南:
    旧代码:
        from src.services.milvus_service import milvus_service
        results = await milvus_service.search_knowledge(embedding, top_k=5)

    新代码:
        from src.repositories import get_knowledge_repository
        knowledge_repo = get_knowledge_repository()
        results = await knowledge_repo.search(embedding, top_k=5)

参考文档:
    - ADR-0009: Repository模式重构
    - src/repositories/README.md
"""

import logging
import time
import warnings
from typing import Any

from pymilvus import AsyncMilvusClient, DataType

from src.core.config import settings
from src.core.exceptions import MilvusConnectionError

logger = logging.getLogger(__name__)


class MilvusService:
    """
    Milvus 向量数据库服务（异步版本）

    .. deprecated:: 0.2.0
        MilvusService已废弃，请使用Repository模式。
        使用 `src.repositories.get_knowledge_repository()` 和
        `src.repositories.get_history_repository()` 替代。

        此类将在6个月后（2025-04-22）删除。
    """

    def __init__(self) -> None:
        warnings.warn(
            "MilvusService is deprecated and will be removed in version 0.3.0. "
            "Use Repository pattern instead: "
            "from src.repositories import get_knowledge_repository, get_history_repository",
            DeprecationWarning,
            stacklevel=2,
        )
        self.client: AsyncMilvusClient | None = None
        self.knowledge_collection_name = settings.milvus_knowledge_collection
        self.history_collection_name = settings.milvus_history_collection

    async def initialize(self) -> None:
        """
        初始化 Milvus 连接和 Collections

        Raises:
            MilvusConnectionError: 连接失败
        """
        try:
            # 构建Milvus URI
            uri = f"http://{settings.milvus_host}:{settings.milvus_port}"

            # 创建异步客户端
            self.client = AsyncMilvusClient(
                uri=uri,
                user=settings.milvus_user,
                password=settings.milvus_password,
                db_name=settings.milvus_database,
                timeout=10,
            )
            logger.info(
                f"✅ Connected to Milvus: {settings.milvus_host}:{settings.milvus_port}"
            )

            # 创建或加载 Collections
            await self._create_knowledge_collection()
            await self._create_history_collection()

        except Exception as e:
            logger.error(f"❌ Failed to connect to Milvus: {e}")
            raise MilvusConnectionError(f"Failed to connect to Milvus: {e}") from e

    async def _create_knowledge_collection(self) -> None:
        """创建知识库 Collection（如果不存在）"""
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        collection_name = self.knowledge_collection_name

        # 检查 Collection 是否存在
        has_collection = await self.client.has_collection(collection_name)
        if has_collection:
            logger.info(f"📂 Collection '{collection_name}' already exists")
            return

        # 定义 Schema - AsyncMilvusClient使用字典格式
        schema = {
            "fields": [
                {
                    "name": "id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 64,
                    "is_primary": True,
                    "description": "文档唯一标识",
                },
                {
                    "name": "text",
                    "dtype": DataType.VARCHAR,
                    "max_length": 10000,
                    "description": "文档文本内容",
                },
                {
                    "name": "embedding",
                    "dtype": DataType.FLOAT_VECTOR,
                    "dim": settings.embedding_dim,
                    "description": "文本向量",
                },
                {
                    "name": "metadata",
                    "dtype": DataType.JSON,
                    "description": "文档元数据",
                },
                {
                    "name": "created_at",
                    "dtype": DataType.INT64,
                    "description": "创建时间戳（秒）",
                },
            ],
            "description": "网站知识库",
            "enable_dynamic_field": False,
        }

        # 索引参数
        index_params = {
            "field_name": "embedding",
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }

        # 创建 Collection（AsyncMilvusClient会自动创建索引并加载）
        await self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )

        logger.info(f"✅ Created and loaded collection: {collection_name}")

    async def _create_history_collection(self) -> None:
        """创建对话历史 Collection（如果不存在）"""
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        collection_name = self.history_collection_name

        # 检查 Collection 是否存在
        has_collection = await self.client.has_collection(collection_name)
        if has_collection:
            logger.info(f"📂 Collection '{collection_name}' already exists")
            return

        # 定义 Schema
        schema = {
            "fields": [
                {
                    "name": "id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 64,
                    "is_primary": True,
                },
                {
                    "name": "session_id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 64,
                    "description": "会话ID",
                },
                {
                    "name": "text",
                    "dtype": DataType.VARCHAR,
                    "max_length": 5000,
                    "description": "对话文本",
                },
                {
                    "name": "embedding",
                    "dtype": DataType.FLOAT_VECTOR,
                    "dim": settings.embedding_dim,
                },
                {
                    "name": "role",
                    "dtype": DataType.VARCHAR,
                    "max_length": 20,
                    "description": "user 或 assistant",
                },
                {
                    "name": "timestamp",
                    "dtype": DataType.INT64,
                    "description": "消息时间戳",
                },
            ],
            "description": "历史对话记忆",
        }

        # 索引参数
        index_params = {
            "field_name": "embedding",
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 64},
        }

        # 创建 Collection
        await self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )

        logger.info(f"✅ Created and loaded collection: {collection_name}")

    async def search_knowledge(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        从知识库检索相关文档

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            score_threshold: 分数阈值（可选，低于阈值的结果会被过滤）

        Returns:
            检索结果列表，每个结果包含: {text, score, metadata}
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        # 执行向量检索（异步）
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}

        results = await self.client.search(
            collection_name=self.knowledge_collection_name,
            data=[query_embedding],
            anns_field="embedding",
            search_params=search_params,
            limit=top_k,
            output_fields=["text", "metadata", "created_at"],
        )

        # 格式化结果
        filtered_results = []
        threshold = score_threshold or settings.vector_score_threshold

        # AsyncMilvusClient返回的结果格式略有不同
        for hit in results[0]:
            # COSINE距离转换为相似度：distance范围[-1,1]，相似度=(1+distance)/2
            similarity_score = 1.0 - (hit["distance"] / 2.0)
            if similarity_score >= threshold:
                filtered_results.append(
                    {
                        "text": hit["entity"].get("text"),
                        "score": similarity_score,  # 返回相似度而非距离
                        "metadata": hit["entity"].get("metadata"),
                    }
                )

        logger.debug(
            f"🔍 Knowledge search: {len(filtered_results)}/{top_k} results above threshold {threshold}"
        )
        return filtered_results

    async def insert_knowledge(
        self,
        documents: list[dict[str, Any]],
    ) -> int:
        """
        批量插入知识库文档

        Args:
            documents: 文档列表，每个文档包含: {id, text, embedding, metadata}

        Returns:
            插入的文档数量
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        if not documents:
            return 0

        # 准备数据 - AsyncMilvusClient使用字典列表格式
        data = []
        current_time = int(time.time())

        for doc in documents:
            data.append({
                "id": doc["id"],
                "text": doc["text"],
                "embedding": doc["embedding"],
                "metadata": doc.get("metadata", {}),
                "created_at": current_time,
            })

        # 异步插入
        await self.client.insert(
            collection_name=self.knowledge_collection_name,
            data=data,
        )

        logger.info(f"📥 Inserted {len(documents)} documents into knowledge base")
        return len(documents)

    async def search_history_by_session(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        按会话ID查询历史对话

        Args:
            session_id: 会话ID
            limit: 返回结果数量

        Returns:
            对话历史列表，按时间排序
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        # 异步查询
        results = await self.client.query(
            collection_name=self.history_collection_name,
            filter=f'session_id == "{session_id}"',
            output_fields=["text", "role", "timestamp"],
            limit=limit,
        )

        # 按时间排序
        sorted_results = sorted(results, key=lambda x: x["timestamp"])
        return sorted_results

    async def health_check(self) -> bool:
        """
        健康检查

        通过尝试列出collections来验证Milvus服务器连接状态

        Returns:
            True if connected and server is responsive, False otherwise
        """
        try:
            if not self.client:
                return False

            # 真正验证Milvus服务器状态：尝试列出collections
            await self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False

    async def close(self) -> None:
        """关闭 Milvus 连接"""
        try:
            if self.client:
                await self.client.close()
                logger.info("✅ Milvus connection closed")
        except Exception as e:
            logger.error(f"Error closing Milvus connection: {e}")


# 全局服务实例
milvus_service = MilvusService()

