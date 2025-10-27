"""
Milvus Repository基类

提供Milvus collection的通用CRUD操作实现。
"""

import logging
from typing import Any, Generic, Type, TypeVar

from pymilvus import AsyncMilvusClient, CollectionSchema, FieldSchema
from pymilvus.milvus_client.index import IndexParams

from src.core.config import settings
from src.core.exceptions import MilvusConnectionError
from src.models.schemas.base import BaseCollectionSchema
from src.repositories.base import BaseRepository
from src.services.milvus_service import milvus_service

logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar("T")
S = TypeVar("S", bound=BaseCollectionSchema)


async def get_milvus_client() -> AsyncMilvusClient:
    """
    获取 Milvus 客户端实例

    Returns:
        AsyncMilvusClient: Milvus 异步客户端
    """
    return milvus_service.client


class BaseMilvusRepository(BaseRepository[T], Generic[T, S]):
    """
    Milvus Repository基类

    封装Milvus collection的通用操作，子类只需提供Schema和类型转换。
    """

    def __init__(
        self,
        client: AsyncMilvusClient,
        schema_class: Type[S],
    ):
        """
        初始化Repository

        Args:
            client: Milvus异步客户端
            schema_class: Collection Schema类
        """
        self.client = client
        self.schema_class = schema_class
        self.collection_name = schema_class.get_collection_name()

    async def initialize(self) -> None:
        """
        初始化Collection（如果不存在则创建，并确保已加载）

        Raises:
            MilvusConnectionError: Collection创建失败
        """
        try:
            # 检查Collection是否存在
            has_collection = await self.client.has_collection(self.collection_name)
            if has_collection:
                logger.info(f"📂 Collection '{self.collection_name}' already exists")
                # 确保Collection已加载到内存
                await self.client.load_collection(self.collection_name)
                logger.info(f"✅ Collection '{self.collection_name}' loaded")
                return

            # 获取Schema配置（字典格式）
            schema_dict = self.schema_class.get_milvus_schema()
            index_params_dict = self.schema_class.get_index_params()

            # 将字典格式的schema转换为CollectionSchema对象
            fields = []
            for field_dict in schema_dict["fields"]:
                # 提取字段参数
                field_kwargs = {
                    "name": field_dict["name"],
                    "dtype": field_dict["dtype"],
                }

                # 添加可选参数
                if "description" in field_dict:
                    field_kwargs["description"] = field_dict["description"]
                if "max_length" in field_dict:
                    field_kwargs["max_length"] = field_dict["max_length"]
                if "dim" in field_dict:
                    field_kwargs["dim"] = field_dict["dim"]
                if "is_primary" in field_dict:
                    field_kwargs["is_primary"] = field_dict["is_primary"]

                fields.append(FieldSchema(**field_kwargs))

            # 创建CollectionSchema对象
            schema = CollectionSchema(
                fields=fields,
                description=schema_dict.get("description", ""),
                enable_dynamic_field=schema_dict.get("enable_dynamic_field", False)
            )

            # 将字典格式的index_params转换为IndexParams对象
            index_params = IndexParams()
            index_params.add_index(
                field_name=index_params_dict["field_name"],
                index_type=index_params_dict["index_type"],
                metric_type=index_params_dict["metric_type"],
                params=index_params_dict.get("params", {}),
            )

            # 创建Collection（AsyncMilvusClient会自动加载）
            await self.client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params,
            )

            logger.info(f"✅ Created and loaded collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize collection {self.collection_name}: {e}")
            raise MilvusConnectionError(
                f"Failed to initialize collection {self.collection_name}: {e}"
            ) from e

    async def _base_search(
        self,
        query_embedding: list[float],
        top_k: int,
        score_threshold: float | None = None,
        output_fields: list[str] | None = None,
        filter_expr: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        基础向量搜索（protected方法，供子类使用）

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            score_threshold: 分数阈值
            output_fields: 要返回的字段
            filter_expr: 过滤表达式

        Returns:
            原始搜索结果列表
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        # 搜索参数
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}

        # 执行搜索
        results = await self.client.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            anns_field="embedding",
            search_params=search_params,
            limit=top_k,
            output_fields=output_fields or ["*"],
            filter=filter_expr,
        )

        # 格式化结果
        filtered_results = []
        threshold = score_threshold or settings.vector_score_threshold

        for hit in results[0]:
            # COSINE距离转换为相似度
            similarity_score = 1.0 - (hit["distance"] / 2.0)
            if similarity_score >= threshold:
                result = {
                    "score": similarity_score,
                    **hit["entity"],  # 展开所有字段
                }
                filtered_results.append(result)

        logger.debug(
            f"🔍 {self.collection_name} search: "
            f"{len(filtered_results)}/{top_k} results above threshold {threshold}"
        )
        return filtered_results

    async def _base_insert(
        self,
        data: list[dict[str, Any]],
    ) -> int:
        """
        基础插入操作（protected方法，供子类使用）

        Args:
            data: 要插入的数据列表

        Returns:
            插入的记录数
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        if not data:
            return 0

        # 执行插入
        await self.client.insert(
            collection_name=self.collection_name,
            data=data,
        )

        logger.info(f"📥 Inserted {len(data)} records into {self.collection_name}")
        return len(data)

    async def _base_query(
        self,
        filter_expr: str,
        output_fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        基础查询操作（protected方法，供子类使用）

        Args:
            filter_expr: 过滤表达式
            output_fields: 要返回的字段
            limit: 返回记录数限制

        Returns:
            查询结果列表
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        # 执行查询
        results = await self.client.query(
            collection_name=self.collection_name,
            filter=filter_expr,
            output_fields=output_fields or ["*"],
            limit=limit,
        )

        logger.debug(f"🔍 Query {self.collection_name}: {len(results)} results")
        return results

    async def delete(self, id: str) -> bool:
        """
        删除记录

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        try:
            await self.client.delete(
                collection_name=self.collection_name,
                filter=f'id == "{id}"',
            )
            logger.info(f"🗑️  Deleted record {id} from {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete record {id}: {e}")
            return False

    async def count(self) -> int:
        """
        获取记录总数

        Returns:
            记录数量
        """
        if not self.client:
            raise MilvusConnectionError("Milvus client not initialized")

        try:
            stats = await self.client.get_collection_stats(self.collection_name)
            row_count = stats.get("row_count", 0)
            return int(row_count)
        except Exception as e:
            logger.error(f"❌ Failed to get count for {self.collection_name}: {e}")
            return 0

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        try:
            if not self.client:
                return False

            # 验证collection存在
            has_collection = await self.client.has_collection(self.collection_name)
            return has_collection
        except Exception as e:
            logger.error(f"❌ Health check failed for {self.collection_name}: {e}")
            return False

