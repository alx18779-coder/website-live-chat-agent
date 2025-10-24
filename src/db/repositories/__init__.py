"""
Repository 层模块

提供数据访问层的 Repository 接口。
"""

from .conversation_repository import ConversationRepository

__all__ = [
    "ConversationRepository",
]
