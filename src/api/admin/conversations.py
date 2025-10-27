"""
对话监控 API

提供对话历史查询和监控接口。
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.admin.dependencies import verify_admin_token
from src.core.config import get_settings
from src.db.base import DatabaseService
from src.db.repositories.conversation_repository import ConversationRepository

router = APIRouter(prefix="/api/admin/conversations", tags=["Conversation Monitoring"])


class ConversationResponse(BaseModel):
    """对话响应"""
    id: str
    session_id: str
    user_message: str
    ai_response: str
    retrieved_docs: Any = Field(default=None, description="检索文档（支持多种格式）")
    confidence_score: Optional[float]
    created_at: datetime


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


async def get_conversation_repository():
    """获取对话历史 Repository - 依赖注入"""
    settings = get_settings()
    db_service = DatabaseService(settings.postgres_url)

    try:
        # 使用 get_session 上下文管理器
        async with db_service.get_session() as session:
            yield ConversationRepository(session)
    finally:
        # 确保连接被正确关闭
        await db_service.close()


@router.get("/history", response_model=ConversationListResponse)
async def get_conversation_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    session_id: Optional[str] = Query(None, description="会话ID筛选"),
    current_user: dict = Depends(verify_admin_token),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
):
    """
    获取对话历史列表

    Args:
        page: 页码
        page_size: 每页数量
        start_date: 开始日期
        end_date: 结束日期
        session_id: 会话ID筛选（模糊匹配）
        current_user: 当前用户信息
        conversation_repo: 对话历史 Repository（依赖注入）

    Returns:
        ConversationListResponse: 对话历史列表响应
    """
    try:

        skip = (page - 1) * page_size

        # 获取对话历史
        conversations = await conversation_repo.get_conversations(
            skip=skip,
            limit=page_size,
            start_date=start_date,
            end_date=end_date,
            session_id=session_id
        )

        # 获取总数
        total = await conversation_repo.count_conversations(
            start_date=start_date,
            end_date=end_date,
            session_id=session_id
        )

        # 格式化响应
        conversation_responses = [
            ConversationResponse(
                id=str(conv.id),
                session_id=conv.session_id,
                user_message=conv.user_message or "",
                ai_response=conv.ai_response or "",
                retrieved_docs=conv.retrieved_docs or [],
                confidence_score=conv.confidence_score,
                created_at=conv.created_at
            )
            for conv in conversations
        ]

        return ConversationListResponse(
            conversations=conversation_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=List[ConversationResponse])
async def get_session_conversations(
    session_id: str,
    current_user: dict = Depends(verify_admin_token),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
):
    """
    获取指定会话的对话记录

    Args:
        session_id: 会话ID
        current_user: 当前用户信息
        conversation_repo: 对话历史 Repository（依赖注入）

    Returns:
        List[ConversationResponse]: 会话对话记录
    """
    try:

        conversations = await conversation_repo.get_conversation_by_session_id(session_id)

        conversation_responses = [
            ConversationResponse(
                id=str(conv.id),
                session_id=conv.session_id,
                user_message=conv.user_message or "",
                ai_response=conv.ai_response or "",
                retrieved_docs=conv.retrieved_docs or [],
                confidence_score=conv.confidence_score,
                created_at=conv.created_at
            )
            for conv in conversations
        ]

        return conversation_responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话对话失败: {str(e)}"
        )
