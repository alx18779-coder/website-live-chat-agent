"""Schema模块"""

from src.models.schemas.base import BaseCollectionSchema
from src.models.schemas.history_schema import HistoryCollectionSchema
from src.models.schemas.knowledge_schema import KnowledgeCollectionSchema

__all__ = [
    "BaseCollectionSchema",
    "KnowledgeCollectionSchema",
    "HistoryCollectionSchema",
]

