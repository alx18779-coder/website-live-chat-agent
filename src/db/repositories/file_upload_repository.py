"""
文件上传记录 Repository

提供文件上传记录的 CRUD 操作。
"""

import logging
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import KnowledgeFileUpload

logger = logging.getLogger(__name__)


class FileUploadRepository:
    """文件上传记录 Repository"""

    def __init__(self, session: AsyncSession):
        """初始化 Repository"""
        self.session = session

    async def create_upload_record(self, data: dict) -> KnowledgeFileUpload:
        """
        创建上传记录

        Args:
            data: 上传记录数据

        Returns:
            KnowledgeFileUpload: 创建的上传记录
        """
        try:
            upload_record = KnowledgeFileUpload(
                filename=data['filename'],
                file_type=data['file_type'],
                file_size=data['file_size'],
                file_path=data.get('file_path'),
                source=data.get('source'),
                version=data.get('version', '1.0'),
                uploader=data['uploader'],
                status=data.get('status', 'pending'),
                progress=data.get('progress', 0)
            )

            self.session.add(upload_record)
            await self.session.commit()
            await self.session.refresh(upload_record)

            logger.info(f"创建上传记录成功: {upload_record.id}")
            return upload_record

        except Exception as e:
            await self.session.rollback()
            logger.error(f"创建上传记录失败: {e}")
            raise

    async def update_status(self, upload_id: str, status: str, progress: int = None, error_message: str = None) -> bool:
        """
        更新上传状态

        Args:
            upload_id: 上传记录 ID
            status: 新状态
            progress: 进度百分比
            error_message: 错误信息

        Returns:
            bool: 更新是否成功
        """
        try:
            result = await self.session.execute(
                select(KnowledgeFileUpload).where(KnowledgeFileUpload.id == upload_id)
            )
            upload_record = result.scalar_one_or_none()

            if not upload_record:
                logger.warning(f"上传记录不存在: {upload_id}")
                return False

            upload_record.status = status
            if progress is not None:
                upload_record.progress = progress
            if error_message is not None:
                upload_record.error_message = error_message

            await self.session.commit()
            logger.info(f"更新上传状态成功: {upload_id} -> {status}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"更新上传状态失败: {e}")
            return False

    async def update_result(self, upload_id: str, result: dict) -> bool:
        """
        更新处理结果

        Args:
            upload_id: 上传记录 ID
            result: 处理结果数据

        Returns:
            bool: 更新是否成功
        """
        try:
            result_query = await self.session.execute(
                select(KnowledgeFileUpload).where(KnowledgeFileUpload.id == upload_id)
            )
            upload_record = result_query.scalar_one_or_none()

            if not upload_record:
                logger.warning(f"上传记录不存在: {upload_id}")
                return False

            # 更新结果字段
            if 'document_count' in result:
                upload_record.document_count = result['document_count']
            if 'milvus_ids' in result:
                upload_record.milvus_ids = result['milvus_ids']
            if 'status' in result:
                upload_record.status = result['status']
            if 'progress' in result:
                upload_record.progress = result['progress']

            await self.session.commit()
            logger.info(f"更新处理结果成功: {upload_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"更新处理结果失败: {e}")
            return False

    async def get_recent_uploads(self, limit: int = 20) -> List[KnowledgeFileUpload]:
        """
        获取最近上传记录

        Args:
            limit: 返回数量限制

        Returns:
            List[KnowledgeFileUpload]: 上传记录列表
        """
        try:
            result = await self.session.execute(
                select(KnowledgeFileUpload)
                .order_by(KnowledgeFileUpload.created_at.desc())
                .limit(limit)
            )

            uploads = result.scalars().all()
            logger.info(f"获取最近上传记录: {len(uploads)} 条")
            return list(uploads)

        except Exception as e:
            logger.error(f"获取最近上传记录失败: {e}")
            return []

    async def get_upload_by_id(self, upload_id: str) -> Optional[KnowledgeFileUpload]:
        """
        根据 ID 获取上传记录

        Args:
            upload_id: 上传记录 ID

        Returns:
            Optional[KnowledgeFileUpload]: 上传记录或 None
        """
        try:
            result = await self.session.execute(
                select(KnowledgeFileUpload).where(KnowledgeFileUpload.id == upload_id)
            )

            upload_record = result.scalar_one_or_none()
            return upload_record

        except Exception as e:
            logger.error(f"获取上传记录失败: {e}")
            return None

    async def delete_upload(self, upload_id: str) -> bool:
        """
        删除上传记录

        Args:
            upload_id: 上传记录 ID

        Returns:
            bool: 删除是否成功
        """
        try:
            result = await self.session.execute(
                delete(KnowledgeFileUpload).where(KnowledgeFileUpload.id == upload_id)
            )

            if result.rowcount == 0:
                logger.warning(f"上传记录不存在: {upload_id}")
                return False

            await self.session.commit()
            logger.info(f"删除上传记录成功: {upload_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"删除上传记录失败: {e}")
            return False

    async def get_uploads_by_status(self, status: str, limit: int = 100) -> List[KnowledgeFileUpload]:
        """
        根据状态获取上传记录

        Args:
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            List[KnowledgeFileUpload]: 上传记录列表
        """
        try:
            result = await self.session.execute(
                select(KnowledgeFileUpload)
                .where(KnowledgeFileUpload.status == status)
                .order_by(KnowledgeFileUpload.created_at.desc())
                .limit(limit)
            )

            uploads = result.scalars().all()
            logger.info(f"获取状态为 {status} 的上传记录: {len(uploads)} 条")
            return list(uploads)

        except Exception as e:
            logger.error(f"获取上传记录失败: {e}")
            return []

    async def get_uploads_by_uploader(self, uploader: str, limit: int = 50) -> List[KnowledgeFileUpload]:
        """
        根据上传者获取上传记录

        Args:
            uploader: 上传者用户名
            limit: 返回数量限制

        Returns:
            List[KnowledgeFileUpload]: 上传记录列表
        """
        try:
            result = await self.session.execute(
                select(KnowledgeFileUpload)
                .where(KnowledgeFileUpload.uploader == uploader)
                .order_by(KnowledgeFileUpload.created_at.desc())
                .limit(limit)
            )

            uploads = result.scalars().all()
            logger.info(f"获取上传者 {uploader} 的上传记录: {len(uploads)} 条")
            return list(uploads)

        except Exception as e:
            logger.error(f"获取上传记录失败: {e}")
            return []



