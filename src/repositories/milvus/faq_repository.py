"""
FAQ Repository

提供FAQ的类型安全数据访问接口。
"""

import logging
import time
from typing import Any

from pymilvus import AsyncMilvusClient

from src.models.entities.faq import FAQ
from src.models.schemas.faq_schema import FAQCollectionSchema
from src.repositories.milvus.base_milvus_repository import BaseMilvusRepository

logger = logging.getLogger(__name__)


class FAQRepository(BaseMilvusRepository[FAQ, FAQCollectionSchema]):
    """
    FAQ Repository - 遵循 Repository 模式
    
    提供类型安全的FAQ数据访问，返回FAQ实体。
    """
    
    def __init__(self, client: AsyncMilvusClient):
        """初始化FAQ Repository"""
        super().__init__(client, FAQCollectionSchema)
    
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        score_threshold: float | None = None,
        language: str | None = None,
    ) -> list[FAQ]:
        """
        搜索FAQ
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            score_threshold: 分数阈值
            language: 语言过滤（可选）
        
        Returns:
            FAQ实体列表（强类型）
        """
        # 构建过滤表达式
        filter_expr = None
        if language:
            filter_expr = f'metadata["language"] == "{language}"'
        
        # 调用基类搜索
        results = await self._base_search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            output_fields=["text", "metadata", "created_at"],
            filter_expr=filter_expr,
        )
        
        # 转换为FAQ实体
        return [
            FAQ(
                text=r["text"],
                score=r["score"],
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]
    
    async def insert(
        self,
        data: list[dict[str, Any]],
    ) -> int:
        """
        插入FAQ数据（BaseRepository 要求的抽象方法）
        
        Args:
            data: FAQ数据列表，格式: {id, text, embedding, metadata}
        
        Returns:
            插入数量
        """
        if not data:
            return 0
        
        current_time = int(time.time())
        formatted_data = [
            {
                "id": item["id"],
                "text": item["text"],
                "embedding": item["embedding"],
                "metadata": item.get("metadata", {}),
                "created_at": current_time,
            }
            for item in data
        ]
        
        return await self._base_insert(formatted_data)
    
    async def insert_faqs(
        self,
        faqs: list[dict[str, Any]],
    ) -> int:
        """
        批量插入FAQ（方法别名，调用 insert）
        
        Args:
            faqs: FAQ列表，格式: {id, text, embedding, metadata}
        
        Returns:
            插入数量
        """
        return await self.insert(faqs)
    
    async def list_faqs(
        self,
        skip: int = 0,
        limit: int = 20,
        language: str | None = None,
    ) -> list[dict]:
        """
        分页查询FAQ列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            language: 语言过滤
        
        Returns:
            list[dict]: FAQ列表
        """
        try:
            expr = "created_at > 0"
            if language:
                expr += f' and metadata["language"] == "{language}"'
            
            results = await self.client.query(
                collection_name=self.collection_name,
                filter=expr,
                output_fields=["id", "text", "metadata", "created_at"],
                limit=limit,
                offset=skip,
            )
            
            return [
                {
                    "id": r["id"],
                    "question": r.get("metadata", {}).get("question", ""),
                    "answer": r.get("metadata", {}).get("answer", ""),
                    "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                    "metadata": r.get("metadata", {}),
                    "created_at": r.get("created_at", 0),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"查询FAQ列表失败: {e}")
            return []
    
    async def count_faqs(self) -> int:
        """
        统计FAQ总数
        
        Returns:
            int: FAQ总数
        """
        return await self.count()
    
    async def get_faq_by_id(self, faq_id: str) -> dict | None:
        """
        根据ID获取FAQ详情
        
        Args:
            faq_id: FAQ ID
        
        Returns:
            dict | None: FAQ详情，不存在返回 None
        """
        try:
            results = await self.client.query(
                collection_name=self.collection_name,
                filter=f'id == "{faq_id}"',
                output_fields=["id", "text", "metadata", "created_at"],
                limit=1
            )
            
            if results:
                result = results[0]
                return {
                    "id": result["id"],
                    "text": result["text"],
                    "question": result.get("metadata", {}).get("question", ""),
                    "answer": result.get("metadata", {}).get("answer", ""),
                    "metadata": result.get("metadata", {}),
                    "created_at": result.get("created_at", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取FAQ详情失败: {e}")
            return None
    
    async def delete_faq(self, faq_id: str) -> bool:
        """
        删除FAQ
        
        Args:
            faq_id: FAQ ID
        
        Returns:
            bool: 删除是否成功
        """
        return await self.delete(faq_id)

