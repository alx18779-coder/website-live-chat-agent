"""
知识库Repository

提供知识库的类型安全数据访问接口。
"""

import logging
import time
from typing import Any

from pymilvus import AsyncMilvusClient

from src.models.entities.knowledge import Knowledge
from src.models.schemas.knowledge_schema import KnowledgeCollectionSchema
from src.repositories.milvus.base_milvus_repository import BaseMilvusRepository

logger = logging.getLogger(__name__)


class KnowledgeRepository(BaseMilvusRepository[Knowledge, KnowledgeCollectionSchema]):
    """
    知识库Repository
    
    提供类型安全的知识库数据访问，返回Knowledge实体。
    """
    
    def __init__(self, client: AsyncMilvusClient):
        """初始化知识库Repository"""
        super().__init__(client, KnowledgeCollectionSchema)
    
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[Knowledge]:
        """
        搜索知识库
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            score_threshold: 分数阈值
        
        Returns:
            知识库实体列表（强类型）
        """
        # 调用基类的通用搜索
        results = await self._base_search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            output_fields=["text", "metadata", "created_at"],
        )
        
        # 转换为Knowledge实体（类型安全）
        return [
            Knowledge(
                text=r["text"],
                score=r["score"],
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]
    
    async def insert(
        self,
        documents: list[dict[str, Any]],
    ) -> int:
        """
        插入知识库文档
        
        Args:
            documents: 文档列表，每个文档包含: {id, text, embedding, metadata}
        
        Returns:
            插入的文档数量
        """
        if not documents:
            return 0
        
        # 准备数据（添加时间戳）
        current_time = int(time.time())
        data = [
            {
                "id": doc["id"],
                "text": doc["text"],
                "embedding": doc["embedding"],
                "metadata": doc.get("metadata", {}),
                "created_at": current_time,
            }
            for doc in documents
        ]
        
        # 调用基类插入
        return await self._base_insert(data)
    
    async def add_document(
        self,
        text: str,
        metadata: dict,
        embedding: list[float]
    ) -> str:
        """
        添加单个文档到知识库
        
        Args:
            text: 文档文本内容
            metadata: 文档元数据
            embedding: 文档向量
            
        Returns:
            文档ID
        """
        import uuid
        
        # 生成唯一文档ID
        doc_id = str(uuid.uuid4())
        
        # 准备数据
        current_time = int(time.time())
        data = [{
            "id": doc_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata,
            "created_at": current_time,
        }]
        
        # 插入到 Milvus
        await self._base_insert(data)
        
        return doc_id
    
    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        search_text: str = ""
    ) -> list[dict]:
        """
        分页查询文档列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            search_text: 搜索文本（在文本内容中搜索）
            
        Returns:
            list[dict]: 文档列表
        """
        try:
            # 构建查询表达式
            expr = "created_at > 0"  # 基础查询条件
            
            if search_text:
                # 在文本内容中搜索（简单实现，实际可能需要更复杂的搜索）
                expr += f' and text like "%{search_text}%"'
            
            # 执行查询
            results = await self.client.query(
                collection_name=self.collection_name,
                filter=expr,
                output_fields=["id", "text", "metadata", "created_at"],
                limit=limit,
                offset=skip,
                order_by_field="created_at",
                order_by_direction="desc"
            )
            
            # 格式化结果
            documents = []
            for result in results:
                documents.append({
                    "id": result["id"],
                    "text": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                    "metadata": result.get("metadata", {}),
                    "created_at": result.get("created_at", 0)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"查询文档列表失败: {e}")
            return []
    
    async def count_documents(self) -> int:
        """
        统计文档总数
        
        使用分页查询来准确统计，避免 Milvus 16384 条限制
        
        Returns:
            int: 文档总数
        """
        try:
            total_count = 0
            offset = 0
            batch_size = 10000  # 每批查询 10000 条
            
            while True:
                # 分页查询文档
                results = await self.client.query(
                    collection_name=self.collection_name,
                    filter="created_at > 0",
                    output_fields=["id"],  # 只查询 ID 字段
                    limit=batch_size,
                    offset=offset
                )
                
                if not results:
                    break
                
                # 累加本批次的数量
                batch_count = len(results)
                total_count += batch_count
                
                # 如果本批次数量小于批次大小，说明已经查完
                if batch_count < batch_size:
                    break
                
                # 准备下一批次
                offset += batch_size
                
                # 防止无限循环（安全限制）
                if offset > 1000000:  # 100万条记录的安全限制
                    logger.warning("文档数量超过安全限制，停止统计")
                    break
            
            logger.debug(f"统计文档总数: {total_count}")
            return total_count
            
        except Exception as e:
            logger.error(f"统计文档数量失败: {e}")
            return 0
    
    async def get_document_by_id(self, doc_id: str) -> dict | None:
        """
        根据ID获取文档详情
        
        Args:
            doc_id: 文档ID
            
        Returns:
            dict | None: 文档详情，不存在返回 None
        """
        try:
            results = await self.client.query(
                collection_name=self.collection_name,
                filter=f'id == "{doc_id}"',
                output_fields=["id", "text", "metadata", "created_at"],
                limit=1
            )
            
            if results:
                result = results[0]
                return {
                    "id": result["id"],
                    "text": result["text"],
                    "metadata": result.get("metadata", {}),
                    "created_at": result.get("created_at", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档详情失败: {e}")
            return None
    
    async def update_document(
        self, 
        doc_id: str, 
        content: str, 
        metadata: dict
    ) -> bool:
        """
        更新文档内容和元数据
        
        Args:
            doc_id: 文档ID
            content: 新的文档内容
            metadata: 新的元数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 先获取原文档
            doc = await self.get_document_by_id(doc_id)
            if not doc:
                return False
            
            # 更新元数据
            updated_metadata = doc.get("metadata", {})
            updated_metadata.update(metadata)
            
            # 重新生成 embedding（重要：确保向量检索使用最新内容）
            from src.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            new_embedding = await embedding_service.get_embedding(content)
            
            # 执行更新（Milvus 的更新操作）
            await self.client.upsert(
                collection_name=self.collection_name,
                data=[{
                    "id": doc_id,
                    "text": content,
                    "metadata": updated_metadata,
                    "embedding": new_embedding,  # 使用新生成的 embedding
                    "created_at": doc.get("created_at", int(time.time()))
                }]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 执行删除
            await self.client.delete(
                collection_name=self.collection_name,
                filter=f'id == "{doc_id}"'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

