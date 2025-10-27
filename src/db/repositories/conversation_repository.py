"""
对话历史 Repository

提供对话历史数据的查询和统计功能。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdminAuditLog, ConversationHistory


class ConversationRepository:
    """对话历史 Repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_conversations(
        self,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> List[ConversationHistory]:
        """
        分页查询对话历史

        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            start_date: 开始日期
            end_date: 结束日期
            session_id: 会话ID（模糊匹配）

        Returns:
            List[ConversationHistory]: 对话历史列表
        """
        query = select(ConversationHistory)

        if start_date:
            query = query.where(ConversationHistory.created_at >= start_date)
        if end_date:
            query = query.where(ConversationHistory.created_at <= end_date)
        if session_id:
            query = query.where(ConversationHistory.session_id.like(f"%{session_id}%"))

        query = query.order_by(desc(ConversationHistory.created_at)).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_conversation_by_session_id(self, session_id: str) -> List[ConversationHistory]:
        """
        根据会话ID获取对话历史

        Args:
            session_id: 会话ID

        Returns:
            List[ConversationHistory]: 对话历史列表
        """
        query = select(ConversationHistory).where(
            ConversationHistory.session_id == session_id
        ).order_by(ConversationHistory.created_at)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_conversations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        统计对话总数

        Args:
            start_date: 开始日期
            end_date: 结束日期
            session_id: 会话ID（模糊匹配）

        Returns:
            int: 对话总数
        """
        query = select(func.count(ConversationHistory.id))

        if start_date:
            query = query.where(ConversationHistory.created_at >= start_date)
        if end_date:
            query = query.where(ConversationHistory.created_at <= end_date)
        if session_id:
            query = query.where(ConversationHistory.session_id.like(f"%{session_id}%"))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取每日统计信息

        Args:
            days: 统计天数

        Returns:
            List[Dict[str, Any]]: 每日统计数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        query = select(
            func.date(ConversationHistory.created_at).label('date'),
            func.count(ConversationHistory.id).label('count')
        ).where(
            ConversationHistory.created_at >= start_date
        ).group_by(
            func.date(ConversationHistory.created_at)
        ).order_by(
            func.date(ConversationHistory.created_at)
        )

        result = await self.session.execute(query)
        return [{"date": str(row.date), "count": row.count} for row in result]

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话统计信息

        Returns:
            Dict[str, Any]: 会话统计数据
        """
        # 总会话数
        total_sessions_query = select(func.count(func.distinct(ConversationHistory.session_id)))
        total_sessions = await self.session.execute(total_sessions_query)
        total_sessions_count = total_sessions.scalar() or 0

        # 今日会话数
        today = datetime.utcnow().date()
        today_sessions_query = select(func.count(func.distinct(ConversationHistory.session_id))).where(
            func.date(ConversationHistory.created_at) == today
        )
        today_sessions = await self.session.execute(today_sessions_query)
        today_sessions_count = today_sessions.scalar() or 0

        # 平均置信度
        avg_confidence_query = select(func.avg(ConversationHistory.confidence_score)).where(
            ConversationHistory.confidence_score.isnot(None)
        )
        avg_confidence = await self.session.execute(avg_confidence_query)
        avg_confidence_score = avg_confidence.scalar() or 0.0

        return {
            "total_sessions": total_sessions_count,
            "today_sessions": today_sessions_count,
            "avg_confidence": round(avg_confidence_score, 3)
        }

    async def log_admin_action(
        self,
        admin_user: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录管理员操作日志

        Args:
            admin_user: 管理员用户名
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
        """
        audit_log = AdminAuditLog(
            admin_user=admin_user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        self.session.add(audit_log)
        await self.session.commit()

    async def create_conversation(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None
    ) -> ConversationHistory:
        """
        创建对话历史记录

        Args:
            session_id: 会话ID（用于关联同一会话的多轮对话）
            user_message: 用户消息内容
            ai_response: AI 回复内容
            retrieved_docs: 检索到的知识库文档列表，格式：
                           [{"content": "...", "score": 0.95, "metadata": {...}}, ...]
            confidence_score: 对话置信度分数（0.0-1.0）

        Returns:
            ConversationHistory: 创建的对话记录对象（包含生成的 ID 和时间戳）

        Raises:
            SQLAlchemyError: 数据库操作失败时抛出

        Example:
            >>> repo = ConversationRepository(session)
            >>> conversation = await repo.create_conversation(
            ...     session_id="session-123",
            ...     user_message="产品价格是多少？",
            ...     ai_response="我们的产品价格为 299 元。",
            ...     retrieved_docs=[{"content": "价格说明...", "score": 0.95}],
            ...     confidence_score=0.92
            ... )
            >>> print(conversation.id)  # UUID对象
        """
        # 创建对话记录对象
        conversation = ConversationHistory(
            session_id=session_id,
            user_message=user_message,
            ai_response=ai_response,
            retrieved_docs=retrieved_docs,
            confidence_score=confidence_score
        )

        # 添加到会话
        self.session.add(conversation)

        # 提交到数据库
        await self.session.commit()

        # 刷新对象以获取数据库生成的字段（id, created_at）
        await self.session.refresh(conversation)

        return conversation
