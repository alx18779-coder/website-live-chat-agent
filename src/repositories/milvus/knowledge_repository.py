"""
知识库Repository

提供知识库的类型安全数据访问接口。
"""

import logging
import time
from typing import Any

from pymilvus import AsyncMilvusClient

from src.models.entities.knowledge import Knowledge
from src.models.schemas.knowledge_schema import KnowledgeCollectionSchema
from src.repositories.milvus.base_milvus_repository import BaseMilvusRepository

logger = logging.getLogger(__name__)


class KnowledgeRepository(BaseMilvusRepository[Knowledge, KnowledgeCollectionSchema]):
    """
    知识库Repository
    
    提供类型安全的知识库数据访问，返回Knowledge实体。
    """
    
    def __init__(self, client: AsyncMilvusClient):
        """初始化知识库Repository"""
        super().__init__(client, KnowledgeCollectionSchema)
    
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[Knowledge]:
        """
        搜索知识库
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            score_threshold: 分数阈值
        
        Returns:
            知识库实体列表（强类型）
        """
        # 调用基类的通用搜索
        results = await self._base_search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            output_fields=["text", "metadata", "created_at"],
        )
        
        # 转换为Knowledge实体（类型安全）
        return [
            Knowledge(
                text=r["text"],
                score=r["score"],
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]
    
    async def insert(
        self,
        documents: list[dict[str, Any]],
    ) -> int:
        """
        插入知识库文档
        
        Args:
            documents: 文档列表，每个文档包含: {id, text, embedding, metadata}
        
        Returns:
            插入的文档数量
        """
        if not documents:
            return 0
        
        # 准备数据（添加时间戳）
        current_time = int(time.time())
        data = [
            {
                "id": doc["id"],
                "text": doc["text"],
                "embedding": doc["embedding"],
                "metadata": doc.get("metadata", {}),
                "created_at": current_time,
            }
            for doc in documents
        ]
        
        # 调用基类插入
        return await self._base_insert(data)

