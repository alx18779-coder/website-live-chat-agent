"""
对话历史Collection Schema定义
"""

from typing import Any, ClassVar

from pymilvus import DataType

from src.core.config import settings
from src.models.schemas.base import BaseCollectionSchema


class HistoryCollectionSchema(BaseCollectionSchema):
    """对话历史Collection Schema"""
    
    COLLECTION_NAME: ClassVar[str] = settings.milvus_history_collection
    
    @classmethod
    def get_milvus_schema(cls) -> dict[str, Any]:
        """
        获取对话历史Milvus schema
        
        字段说明:
        - id: 消息唯一标识（主键）
        - session_id: 会话ID
        - role: 角色（user/assistant）
        - text: 消息文本
        - embedding: 文本向量
        - timestamp: 消息时间戳
        """
        return {
            "fields": [
                {
                    "name": "id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 64,
                    "is_primary": True,
                    "description": "消息唯一标识",
                },
                {
                    "name": "session_id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 128,
                    "description": "会话ID",
                },
                {
                    "name": "role",
                    "dtype": DataType.VARCHAR,
                    "max_length": 20,
                    "description": "角色: user/assistant",
                },
                {
                    "name": "text",
                    "dtype": DataType.VARCHAR,
                    "max_length": 10000,
                    "description": "消息文本",
                },
                {
                    "name": "embedding",
                    "dtype": DataType.FLOAT_VECTOR,
                    "dim": settings.embedding_dim,
                    "description": "文本向量",
                },
                {
                    "name": "timestamp",
                    "dtype": DataType.INT64,
                    "description": "消息时间戳（秒）",
                },
            ],
            "description": "对话历史记录",
            "enable_dynamic_field": False,
        }
    
    @classmethod
    def get_index_params(cls) -> dict[str, Any]:
        """获取向量索引配置"""
        return {
            "field_name": "embedding",
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }

