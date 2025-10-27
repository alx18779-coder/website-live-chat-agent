"""
文件上传处理服务

处理文件上传、解析、向量化和存储的完整流程。
"""

import asyncio
import logging
import os
import tempfile
from typing import Dict, List, Optional
from datetime import datetime

from src.services.file_parser import FileParser
from src.services.embedding_service import get_embedding_service
from src.repositories.milvus.knowledge_repository import KnowledgeRepository
from src.repositories.milvus.base_milvus_repository import get_milvus_client
from src.db.repositories.file_upload_repository import FileUploadRepository
from src.db.base import DatabaseService

logger = logging.getLogger(__name__)


class FileUploadProcessor:
    """文件上传处理服务"""
    
    def __init__(self, db_service: DatabaseService):
        """初始化文件上传处理器"""
        self.db_service = db_service
        self.file_parser = FileParser()
        self.max_retries = 3
    
    async def process_file(self, upload_record_id: str) -> bool:
        """
        处理上传的文件
        
        Args:
            upload_record_id: 上传记录 ID
            
        Returns:
            bool: 处理是否成功
        """
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                return await self._do_process(upload_record_id)
            except Exception as e:
                retry_count += 1
                logger.error(f"处理文件失败 (重试 {retry_count}/{self.max_retries}): {e}")
                
                if retry_count >= self.max_retries:
                    # 标记为失败
                    await self._update_status(
                        upload_record_id,
                        status="failed",
                        error_message=str(e)
                    )
                    return False
                else:
                    # 等待后重试
                    await asyncio.sleep(2 ** retry_count)
        
        return False
    
    async def _do_process(self, upload_record_id: str) -> bool:
        """执行文件处理逻辑"""
        try:
            # 1. 获取上传记录
            async with self.db_service.get_session() as session:
                upload_repo = FileUploadRepository(session)
                upload_record = await upload_repo.get_upload_by_id(upload_record_id)
                
                if not upload_record:
                    logger.error(f"上传记录不存在: {upload_record_id}")
                    return False
                
                # 2. 更新状态为处理中
                await upload_repo.update_status(
                    upload_record_id,
                    status="processing",
                    progress=10
                )
            
            # 3. 读取文件内容
            if not upload_record.file_path or not os.path.exists(upload_record.file_path):
                raise FileNotFoundError(f"文件不存在: {upload_record.file_path}")
            
            with open(upload_record.file_path, 'rb') as f:
                file_content = f.read()
            
            # 4. 解析文件内容
            await self._update_status(upload_record_id, status="processing", progress=30)
            parsed_result = await self.file_parser.parse_file(file_content, upload_record.filename)
            
            chunks = parsed_result['chunks']
            metadata = parsed_result['metadata']
            
            if not chunks:
                raise ValueError("文件解析后没有有效内容")
            
            logger.info(f"文件解析完成: {len(chunks)} 个分块")
            
            # 5. 生成向量并存储到 Milvus
            await self._update_status(upload_record_id, status="processing", progress=50)
            milvus_ids = await self._store_to_milvus(chunks, upload_record, metadata)
            
            # 6. 更新处理结果
            await self._update_status(upload_record_id, status="processing", progress=90)
            await self._update_result(upload_record_id, {
                'document_count': len(chunks),
                'milvus_ids': milvus_ids,
                'status': 'completed',
                'progress': 100
            })
            
            # 7. 清理临时文件
            try:
                os.remove(upload_record.file_path)
                logger.info(f"清理临时文件: {upload_record.file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            
            logger.info(f"文件处理完成: {upload_record_id}")
            return True
            
        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            await self._update_status(
                upload_record_id,
                status="failed",
                error_message=str(e)
            )
            return False
    
    async def _store_to_milvus(self, chunks: List[str], upload_record, metadata: Dict) -> List[str]:
        """将分块存储到 Milvus"""
        try:
            # 获取 Milvus 客户端和知识库仓库
            milvus_client = await get_milvus_client()
            knowledge_repo = KnowledgeRepository(milvus_client)
            
            # 获取嵌入服务
            embedding_service = get_embedding_service()
            
            milvus_ids = []
            
            # 批量处理分块
            for i, chunk in enumerate(chunks):
                try:
                    # 生成嵌入向量
                    embedding = await embedding_service.get_embedding(chunk)
                    
                    # 构建文档元数据
                    doc_metadata = {
                        'filename': upload_record.filename,
                        'file_type': upload_record.file_type,
                        'source': upload_record.source,
                        'version': upload_record.version,
                        'uploader': upload_record.uploader,
                        'upload_id': str(upload_record.id),
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'created_at': int(datetime.utcnow().timestamp())
                    }
                    
                    # 存储到 Milvus
                    doc_id = await knowledge_repo.add_document(
                        text=chunk,
                        metadata=doc_metadata,
                        embedding=embedding
                    )
                    
                    milvus_ids.append(doc_id)
                    logger.debug(f"存储分块 {i+1}/{len(chunks)} 到 Milvus: {doc_id}")
                    
                except Exception as e:
                    logger.error(f"存储分块 {i+1} 失败: {e}")
                    continue
            
            if not milvus_ids:
                raise ValueError("没有成功存储任何分块到 Milvus")
            
            logger.info(f"成功存储 {len(milvus_ids)} 个分块到 Milvus")
            return milvus_ids
            
        except Exception as e:
            logger.error(f"存储到 Milvus 失败: {e}")
            raise
    
    async def _update_status(self, upload_id: str, status: str, progress: int = None, error_message: str = None):
        """更新上传状态"""
        try:
            async with self.db_service.get_session() as session:
                upload_repo = FileUploadRepository(session)
                await upload_repo.update_status(upload_id, status, progress, error_message)
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    async def _update_result(self, upload_id: str, result: Dict):
        """更新处理结果"""
        try:
            async with self.db_service.get_session() as session:
                upload_repo = FileUploadRepository(session)
                await upload_repo.update_result(upload_id, result)
        except Exception as e:
            logger.error(f"更新结果失败: {e}")
    
    async def rollback_upload(self, upload_id: str) -> bool:
        """
        回滚上传（删除相关文档）
        
        Args:
            upload_id: 上传记录 ID
            
        Returns:
            bool: 回滚是否成功
        """
        try:
            # 获取上传记录
            async with self.db_service.get_session() as session:
                upload_repo = FileUploadRepository(session)
                upload_record = await upload_repo.get_upload_by_id(upload_id)
                
                if not upload_record:
                    logger.warning(f"上传记录不存在: {upload_id}")
                    return False
                
                # 从 Milvus 删除相关文档
                if upload_record.milvus_ids:
                    milvus_client = await get_milvus_client()
                    knowledge_repo = KnowledgeRepository(milvus_client)
                    
                    for doc_id in upload_record.milvus_ids:
                        try:
                            await knowledge_repo.delete_document(doc_id)
                            logger.debug(f"删除 Milvus 文档: {doc_id}")
                        except Exception as e:
                            logger.warning(f"删除 Milvus 文档失败 {doc_id}: {e}")
                
                # 删除上传记录
                success = await upload_repo.delete_upload(upload_id)
                
                if success:
                    logger.info(f"回滚上传成功: {upload_id}")
                else:
                    logger.error(f"回滚上传失败: {upload_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"回滚上传失败: {e}")
            return False
    
    async def retry_upload(self, upload_id: str) -> bool:
        """
        重试失败的上传
        
        Args:
            upload_id: 上传记录 ID
            
        Returns:
            bool: 重试是否成功
        """
        try:
            # 重置状态
            await self._update_status(upload_id, status="pending", progress=0, error_message=None)
            
            # 重新处理
            return await self.process_file(upload_id)
            
        except Exception as e:
            logger.error(f"重试上传失败: {e}")
            return False



