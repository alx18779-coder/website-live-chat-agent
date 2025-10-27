"""
对话历史Repository

提供对话历史的类型安全数据访问接口。
"""

import logging
import time
from typing import Any

from pymilvus import AsyncMilvusClient

from src.models.entities.history import ConversationHistory
from src.models.schemas.history_schema import HistoryCollectionSchema
from src.repositories.milvus.base_milvus_repository import BaseMilvusRepository

logger = logging.getLogger(__name__)


class HistoryRepository(BaseMilvusRepository[ConversationHistory, HistoryCollectionSchema]):
    """
    对话历史Repository

    提供类型安全的对话历史数据访问，返回ConversationHistory实体。
    """

    def __init__(self, client: AsyncMilvusClient):
        """初始化对话历史Repository"""
        super().__init__(client, HistoryCollectionSchema)

    async def search(
        self,
        query_embedding: list[float],
        session_id: str | None = None,
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> list[ConversationHistory]:
        """
        搜索对话历史

        Args:
            query_embedding: 查询向量
            session_id: 会话ID（可选，用于过滤）
            top_k: 返回结果数量
            score_threshold: 分数阈值

        Returns:
            对话历史实体列表（强类型）
        """
        # 构建过滤表达式
        filter_expr = None
        if session_id:
            filter_expr = f'session_id == "{session_id}"'

        # 调用基类的通用搜索
        results = await self._base_search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            output_fields=["role", "text", "timestamp", "session_id"],
            filter_expr=filter_expr,
        )

        # 转换为ConversationHistory实体（类型安全）
        return [
            ConversationHistory(
                role=r["role"],
                text=r["text"],
                timestamp=r["timestamp"],
            )
            for r in results
        ]

    async def search_by_session(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[ConversationHistory]:
        """
        按会话ID查询历史对话（特殊方法）

        Args:
            session_id: 会话ID
            limit: 返回记录数限制

        Returns:
            对话历史实体列表（按时间排序）
        """
        # 使用基类的query方法
        results = await self._base_query(
            filter_expr=f'session_id == "{session_id}"',
            output_fields=["role", "text", "timestamp"],
            limit=limit,
        )

        # 按时间戳排序（升序）
        sorted_results = sorted(results, key=lambda x: x["timestamp"])

        # 转换为ConversationHistory实体
        return [
            ConversationHistory(
                role=r["role"],
                text=r["text"],
                timestamp=r["timestamp"],
            )
            for r in sorted_results
        ]

    async def insert(
        self,
        messages: list[dict[str, Any]],
    ) -> int:
        """
        插入对话历史

        Args:
            messages: 消息列表，每个消息包含: {id, session_id, role, text, embedding}

        Returns:
            插入的消息数量
        """
        if not messages:
            return 0

        # 准备数据（添加时间戳）
        current_time = int(time.time())
        data = [
            {
                "id": msg["id"],
                "session_id": msg["session_id"],
                "role": msg["role"],
                "text": msg["text"],
                "embedding": msg["embedding"],
                "timestamp": msg.get("timestamp", current_time),
            }
            for msg in messages
        ]

        # 调用基类插入
        return await self._base_insert(data)

