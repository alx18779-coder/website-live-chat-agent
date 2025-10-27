"""
FAQ管理 API

提供FAQ的上传、查询、删除等管理功能。
"""

import logging
import time
import uuid
from typing import Dict, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel

from src.api.admin.dependencies import verify_admin_token
from src.core.config import settings
from src.repositories.milvus.base_milvus_repository import get_milvus_client
from src.repositories.milvus.faq_repository import FAQRepository
from src.services.faq_csv_parser import FAQCSVParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/faq", tags=["FAQ Management"])

# 文件大小限制（字节）
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024

# 导入任务状态存储（生产环境应使用 Redis）
import_tasks: Dict[str, dict] = {}


async def process_faq_import_task(
    task_id: str,
    file_content: bytes,
    text_cols: list[str],
    embed_cols: list[str],
    text_template: str,
    language: str
):
    """
    后台任务：处理FAQ导入

    Args:
        task_id: 任务ID
        file_content: CSV文件内容
        text_cols: 文本列
        embed_cols: embedding列
        text_template: 文本模板
        language: 语言
    """
    try:
        # 更新状态为处理中
        import_tasks[task_id]["status"] = "processing"
        import_tasks[task_id]["message"] = "正在解析CSV..."

        # 解析CSV
        parser = FAQCSVParser()
        faqs = await parser.process_csv(
            file_content=file_content,
            text_columns=text_cols,
            embedding_columns=embed_cols,
            text_template=text_template,
            language=language,
        )

        import_tasks[task_id]["total"] = len(faqs)
        import_tasks[task_id]["message"] = f"正在导入 {len(faqs)} 条FAQ..."

        if not faqs:
            import_tasks[task_id]["status"] = "failed"
            import_tasks[task_id]["error"] = "CSV文件为空或解析失败"
            return

        # 插入到Milvus
        milvus_client = await get_milvus_client()
        faq_repo = FAQRepository(milvus_client)
        await faq_repo.initialize()

        inserted_count = await faq_repo.insert_faqs(faqs)

        # 更新状态为完成
        import_tasks[task_id]["status"] = "completed"
        import_tasks[task_id]["progress"] = 100
        import_tasks[task_id]["processed"] = len(faqs)
        import_tasks[task_id]["imported_count"] = inserted_count
        import_tasks[task_id]["message"] = f"成功导入 {inserted_count} 条FAQ"

        logger.info(f"✅ FAQ导入任务 {task_id} 完成，导入 {inserted_count} 条")

    except Exception as e:
        logger.error(f"❌ FAQ导入任务 {task_id} 失败: {e}")
        import_tasks[task_id]["status"] = "failed"
        import_tasks[task_id]["error"] = str(e)
        import_tasks[task_id]["message"] = f"导入失败: {str(e)}"


class CSVPreviewResponse(BaseModel):
    """CSV预览响应"""
    columns: list[str]
    preview_rows: list[dict]
    total_rows: int
    detected_language: str


class FAQImportRequest(BaseModel):
    """FAQ导入请求"""
    text_columns: list[str]
    embedding_columns: list[str]
    text_template: str = "{question}\n答：{answer}"
    language: str = "zh"


class FAQImportResponse(BaseModel):
    """FAQ导入响应（立即返回任务ID）"""
    task_id: str
    message: str


class FAQImportStatusResponse(BaseModel):
    """FAQ导入状态响应"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    total: int
    processed: int
    imported_count: int
    message: str
    error: Optional[str] = None


class FAQListResponse(BaseModel):
    """FAQ列表响应"""
    faqs: list[dict]
    total: int


@router.post("/upload/preview", response_model=CSVPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_admin_token)
) -> CSVPreviewResponse:
    """
    预览CSV文件（第一步）

    返回CSV的列信息和前5行数据，供用户配置
    """
    try:
        if not file.filename or not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仅支持CSV格式文件"
            )

        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()  # 获取文件大小
        file.file.seek(0)  # 重置到开头

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制（最大 {settings.max_upload_size_mb} MB）"
            )

        content = await file.read()
        parser = FAQCSVParser()
        preview = await parser.parse_csv_preview(content)

        return CSVPreviewResponse(**preview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览CSV失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览失败: {str(e)}"
        )


@router.post("/upload/import", response_model=FAQImportResponse)
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    text_columns: str = Form(""),
    embedding_columns: str = Form(""),
    text_template: str = Form("{question}\n答：{answer}"),
    language: str = Form("zh"),
    current_user: dict = Depends(verify_admin_token)
) -> FAQImportResponse:
    """
    导入CSV到FAQ库（异步后台处理）

    立即返回任务ID，导入在后台执行

    Args:
        background_tasks: FastAPI 后台任务
        file: CSV文件
        text_columns: 用于生成text的列名（逗号分隔）
        embedding_columns: 用于生成embedding的列名（逗号分隔）
        text_template: 文本拼接模板
        language: 语言标记

    Returns:
        FAQImportResponse: 任务ID和提示信息
    """
    try:
        # 检查文件大小
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制（最大 {settings.max_upload_size_mb} MB）"
            )

        content = await file.read()

        # 解析列配置
        text_cols = [col.strip() for col in text_columns.split(',') if col.strip()]
        embed_cols = [col.strip() for col in embedding_columns.split(',') if col.strip()]

        if not text_cols or not embed_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="text_columns和embedding_columns不能为空"
            )

        # 创建任务ID
        task_id = str(uuid.uuid4())

        # 初始化任务状态
        import_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "total": 0,
            "processed": 0,
            "imported_count": 0,
            "message": "任务已创建，等待处理...",
            "error": None,
            "created_at": time.time()
        }

        # 添加后台任务
        background_tasks.add_task(
            process_faq_import_task,
            task_id,
            content,
            text_cols,
            embed_cols,
            text_template,
            language
        )

        logger.info(f"📤 创建FAQ导入任务: {task_id}")

        return FAQImportResponse(
            task_id=task_id,
            message="导入任务已创建，请使用task_id查询导入进度"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建FAQ导入任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )


@router.get("/upload/import/{task_id}/status", response_model=FAQImportStatusResponse)
async def get_import_status(
    task_id: str,
    current_user: dict = Depends(verify_admin_token)
) -> FAQImportStatusResponse:
    """
    查询FAQ导入任务状态

    Args:
        task_id: 任务ID
        current_user: 当前用户

    Returns:
        FAQImportStatusResponse: 任务状态信息
    """
    task = import_tasks.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )

    return FAQImportStatusResponse(**task)


@router.get("/list", response_model=FAQListResponse)
async def list_faqs(
    skip: int = 0,
    limit: int = 20,
    language: Optional[str] = None,
    current_user: dict = Depends(verify_admin_token)
) -> FAQListResponse:
    """获取FAQ列表"""
    try:
        client = await get_milvus_client()
        faq_repo = FAQRepository(client)
        faqs = await faq_repo.list_faqs(skip=skip, limit=limit, language=language)
        total = await faq_repo.count_faqs()

        return FAQListResponse(faqs=faqs, total=total)

    except Exception as e:
        logger.error(f"获取FAQ列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取FAQ列表失败: {str(e)}"
        )


@router.get("/{faq_id}")
async def get_faq(
    faq_id: str,
    current_user: dict = Depends(verify_admin_token)
) -> dict:
    """获取FAQ详情"""
    try:
        client = await get_milvus_client()
        faq_repo = FAQRepository(client)
        faq = await faq_repo.get_faq_by_id(faq_id)

        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ不存在"
            )

        return faq

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取FAQ详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取FAQ详情失败: {str(e)}"
        )


@router.delete("/{faq_id}")
async def delete_faq(
    faq_id: str,
    current_user: dict = Depends(verify_admin_token)
) -> dict:
    """删除FAQ"""
    try:
        client = await get_milvus_client()
        faq_repo = FAQRepository(client)
        success = await faq_repo.delete_faq(faq_id)

        if success:
            return {"message": "FAQ删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ不存在"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除FAQ失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除FAQ失败: {str(e)}"
        )

