"""
统计报表 API

提供运营数据统计和分析接口。
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.admin.dependencies import verify_admin_token
from src.core.config import get_settings
from src.db.base import DatabaseService
from src.db.repositories.conversation_repository import ConversationRepository

router = APIRouter(prefix="/api/admin/analytics", tags=["Analytics"])


class OverviewStatsResponse(BaseModel):
    """总览统计响应"""
    total_sessions: int
    today_sessions: int
    avg_confidence: float


class DailyStatsResponse(BaseModel):
    """每日统计响应"""
    date: str
    count: int


class AnalyticsResponse(BaseModel):
    """统计响应"""
    overview: OverviewStatsResponse
    daily_stats: List[DailyStatsResponse]


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


@router.get("/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(
    current_user: dict = Depends(verify_admin_token),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
):
    """
    获取总览统计

    Args:
        current_user: 当前用户信息
        conversation_repo: 对话历史 Repository（依赖注入）

    Returns:
        OverviewStatsResponse: 总览统计数据
    """
    try:
        # 获取会话统计
        session_stats = await conversation_repo.get_session_stats()

        return OverviewStatsResponse(
            total_sessions=session_stats["total_sessions"],
            today_sessions=session_stats["today_sessions"],
            avg_confidence=session_stats["avg_confidence"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取总览统计失败: {str(e)}"
        )


@router.get("/daily", response_model=List[DailyStatsResponse])
async def get_daily_stats(
    days: int = 7,
    current_user: dict = Depends(verify_admin_token),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
):
    """
    获取每日统计

    Args:
        days: 统计天数
        current_user: 当前用户信息
        conversation_repo: 对话历史 Repository（依赖注入）

    Returns:
        List[DailyStatsResponse]: 每日统计数据
    """
    try:
        # 获取每日统计
        daily_stats = await conversation_repo.get_daily_stats(days=days)

        return [
            DailyStatsResponse(date=stat["date"], count=stat["count"])
            for stat in daily_stats
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每日统计失败: {str(e)}"
        )
