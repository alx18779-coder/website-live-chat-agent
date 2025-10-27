"""
知识库Collection Schema定义
"""

from typing import Any, ClassVar

from pymilvus import DataType

from src.core.config import settings
from src.models.schemas.base import BaseCollectionSchema


class KnowledgeCollectionSchema(BaseCollectionSchema):
    """知识库Collection Schema"""

    COLLECTION_NAME: ClassVar[str] = settings.milvus_knowledge_collection

    @classmethod
    def get_milvus_schema(cls) -> dict[str, Any]:
        """
        获取知识库Milvus schema

        字段说明:
        - id: 文档唯一标识（主键）
        - text: 文档文本内容
        - embedding: 文本向量
        - metadata: 文档元数据（JSON）
        - created_at: 创建时间戳
        """
        return {
            "fields": [
                {
                    "name": "id",
                    "dtype": DataType.VARCHAR,
                    "max_length": 64,
                    "is_primary": True,
                    "description": "文档唯一标识",
                },
                {
                    "name": "text",
                    "dtype": DataType.VARCHAR,
                    "max_length": 10000,
                    "description": "文档文本内容",
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
                    "description": "文档元数据",
                },
                {
                    "name": "created_at",
                    "dtype": DataType.INT64,
                    "description": "创建时间戳（秒）",
                },
            ],
            "description": "网站知识库",
            "enable_dynamic_field": False,
        }

    @classmethod
    def get_index_params(cls) -> dict[str, Any]:
        """
        获取向量索引配置

        使用COSINE相似度和IVF_FLAT索引
        """
        return {
            "field_name": "embedding",
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }

