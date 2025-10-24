"""
FAQ Collection Schema定义
"""

from typing import Any, ClassVar

from pymilvus import DataType

from src.core.config import settings
from src.models.schemas.base import BaseCollectionSchema


class FAQCollectionSchema(BaseCollectionSchema):
    """FAQ Collection Schema - 支持灵活的列配置"""
    
    COLLECTION_NAME: ClassVar[str] = settings.milvus_faq_collection
    
    @classmethod
    def get_milvus_schema(cls) -> dict[str, Any]:
        """
        FAQ Schema定义
        
        字段说明:
        - id: FAQ唯一标识（主键）
        - text: 拼接后的文本内容（用于展示和二次检索）
        - embedding: 向量（用于相似度检索）
        - metadata: 原始数据和元信息
            - question: 原始问题
            - answer: 原始答案
            - language: 语言（zh/en）
            - category: 分类
            - text_template: 使用的拼接模板
            - embedding_source: embedding生成来源（question/answer/both）
        - created_at: 创建时间戳
        """
        return {
            "fields": [
                {
                    "name": "id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 64,
                    "is_primary": True,
                    "description": "FAQ唯一标识",
                },
                {
                    "name": "text",
                    "dtype": DataType.VARCHAR,
                    "max_length": 10000,
                    "description": "拼接后的文本内容",
                },
                {
                    "name": "embedding",
                    "dtype": DataType.FLOAT_VECTOR,
                    "dim": settings.embedding_dim,
                    "description": "文本向量",
                },
                {
                    "name": "metadata",
                    "dtype": DataType.JSON,
                    "description": "原始数据和元信息",
                },
                {
                    "name": "created_at",
                    "dtype": DataType.INT64,
                    "description": "创建时间戳（秒）",
                },
            ],
            "description": "FAQ知识库",
            "enable_dynamic_field": False,
        }
    
    @classmethod
    def get_index_params(cls) -> dict[str, Any]:
        """向量索引配置"""
        return {
            "field_name": "embedding",
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }

