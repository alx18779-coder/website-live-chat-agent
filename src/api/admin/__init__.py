"""
管理 API 模块

提供管理员认证、知识库管理、对话监控、统计报表等接口。
"""

from .auth import router as auth_router
from .dependencies import verify_admin_token
from .knowledge import router as knowledge_router
from .conversations import router as conversations_router
from .analytics import router as analytics_router
from .settings import router as settings_router

__all__ = [
    "auth_router",
    "knowledge_router", 
    "conversations_router",
    "analytics_router",
    "settings_router",
    "verify_admin_token",
]
