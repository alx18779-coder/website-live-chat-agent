"""
知识库管理 API

提供知识库文档的 CRUD 操作接口和文件上传功能。
"""

import os
import tempfile
import uuid
import magic
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form, BackgroundTasks
from pydantic import BaseModel

from src.api.admin.dependencies import verify_admin_token
from src.repositories.milvus.knowledge_repository import KnowledgeRepository
from src.repositories.milvus.base_milvus_repository import get_milvus_client
from src.db.base import DatabaseService
from src.db.repositories.file_upload_repository import FileUploadRepository
from src.services.file_upload_processor import FileUploadProcessor
from src.core.config import get_settings

router = APIRouter(prefix="/api/admin/knowledge", tags=["Knowledge Management"])


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    text: str
    metadata: dict
    created_at: int


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentUpdateRequest(BaseModel):
    """文档更新请求"""
    content: str
    metadata: dict


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    upload_id: str
    filename: str
    status: str
    message: str


class UploadStatusResponse(BaseModel):
    """上传状态响应"""
    upload_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    progress: int
    document_count: int
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]


class FilePreviewResponse(BaseModel):
    """文件预览响应"""
    filename: str
    file_type: str
    chunks: List[str]
    total_chunks: int
    estimated_tokens: int


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(verify_admin_token)
):
    """
    获取文档列表
    
    Args:
        page: 页码
        page_size: 每页数量
        search: 搜索关键词
        current_user: 当前用户信息
        
    Returns:
        DocumentListResponse: 文档列表响应
    """
    try:
        client = await get_milvus_client()
        knowledge_repo = KnowledgeRepository(client)
        
        skip = (page - 1) * page_size
        
        # 获取文档列表
        documents = await knowledge_repo.list_documents(
            skip=skip,
            limit=page_size,
            search_text=search or ""
        )
        
        # 获取总数
        total = await knowledge_repo.count_documents()
        
        # 格式化响应
        document_responses = [
            DocumentResponse(
                id=doc["id"],
                text=doc["text"],
                metadata=doc.get("metadata", {}),
                created_at=doc.get("created_at", 0)
            )
            for doc in documents
        ]
        
        return DocumentListResponse(
            documents=document_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """
    获取文档详情
    
    Args:
        doc_id: 文档ID
        current_user: 当前用户信息
        
    Returns:
        DocumentResponse: 文档详情
        
    Raises:
        HTTPException: 文档不存在时抛出 404 错误
    """
    try:
        client = await get_milvus_client()
        knowledge_repo = KnowledgeRepository(client)
        
        document = await knowledge_repo.get_document_by_id(doc_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        return DocumentResponse(
            id=document["id"],
            text=document["text"],
            metadata=document.get("metadata", {}),
            created_at=document.get("created_at", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档详情失败: {str(e)}"
        )


@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    request: DocumentUpdateRequest,
    current_user: dict = Depends(verify_admin_token)
):
    """
    更新文档
    
    Args:
        doc_id: 文档ID
        request: 更新请求
        current_user: 当前用户信息
        
    Returns:
        dict: 更新结果
        
    Raises:
        HTTPException: 文档不存在或更新失败时抛出错误
    """
    try:
        client = await get_milvus_client()
        knowledge_repo = KnowledgeRepository(client)
        
        # 检查文档是否存在
        existing_doc = await knowledge_repo.get_document_by_id(doc_id)
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 更新文档
        success = await knowledge_repo.update_document(
            doc_id=doc_id,
            content=request.content,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新文档失败"
            )
        
        return {"message": "文档更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档失败: {str(e)}"
        )


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """
    删除文档
    
    Args:
        doc_id: 文档ID
        current_user: 当前用户信息
        
    Returns:
        dict: 删除结果
        
    Raises:
        HTTPException: 文档不存在或删除失败时抛出错误
    """
    try:
        client = await get_milvus_client()
        knowledge_repo = KnowledgeRepository(client)
        
        # 检查文档是否存在
        existing_doc = await knowledge_repo.get_document_by_id(doc_id)
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 删除文档
        success = await knowledge_repo.delete_document(doc_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除文档失败"
            )
        
        return {"message": "文档删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


# 文件上传相关 API

@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    source: Optional[str] = Form(None),
    version: Optional[str] = Form("1.0"),
    current_user: dict = Depends(verify_admin_token)
):
    """
    上传文件到知识库
    
    Args:
        background_tasks: 后台任务
        files: 上传的文件列表
        source: 文件来源
        version: 文件版本
        current_user: 当前用户信息
        
    Returns:
        List[FileUploadResponse]: 上传结果列表
    """
    try:
        settings = get_settings()
        db_service = DatabaseService(settings.postgres_url)
        
        upload_responses = []
        
        async with db_service.get_session() as session:
            upload_repo = FileUploadRepository(session)
            
            for file in files:
                try:
                    # 验证文件
                    if not file.filename:
                        continue
                    
                    # 检查文件大小
                    file_content = await file.read()
                    if len(file_content) > 10 * 1024 * 1024:  # 10MB
                        upload_responses.append(FileUploadResponse(
                            upload_id="",
                            filename=file.filename,
                            status="failed",
                            message="文件大小超过限制 (10MB)"
                        ))
                        continue
                    
                    # 保存文件到临时目录
                    temp_dir = tempfile.gettempdir()
                    temp_filename = f"{uuid.uuid4()}_{file.filename}"
                    temp_path = os.path.join(temp_dir, temp_filename)
                    
                    with open(temp_path, 'wb') as f:
                        f.write(file_content)
                    
                    # 检测文件类型
                    file_type = _detect_file_type(file_content, file.filename)
                    
                    # 创建上传记录
                    upload_data = {
                        'filename': file.filename,
                        'file_type': file_type,
                        'file_size': len(file_content),
                        'file_path': temp_path,
                        'source': source,
                        'version': version,
                        'uploader': current_user.get('sub', 'admin'),
                        'status': 'pending',
                        'progress': 0
                    }
                    
                    upload_record = await upload_repo.create_upload_record(upload_data)
                    
                    # 添加后台处理任务
                    processor = FileUploadProcessor(db_service)
                    background_tasks.add_task(processor.process_file, str(upload_record.id))
                    
                    upload_responses.append(FileUploadResponse(
                        upload_id=str(upload_record.id),
                        filename=file.filename,
                        status="pending",
                        message="文件上传成功，正在处理..."
                    ))
                    
                except Exception as e:
                    upload_responses.append(FileUploadResponse(
                        upload_id="",
                        filename=file.filename,
                        status="failed",
                        message=f"上传失败: {str(e)}"
                    ))
        
        return upload_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/uploads", response_model=List[UploadStatusResponse])
async def list_uploads(
    limit: int = Query(20, le=100, description="返回数量限制"),
    current_user: dict = Depends(verify_admin_token)
):
    """
    获取最近上传记录
    
    Args:
        limit: 返回数量限制
        current_user: 当前用户信息
        
    Returns:
        List[UploadStatusResponse]: 上传记录列表
    """
    try:
        settings = get_settings()
        db_service = DatabaseService(settings.postgres_url)
        
        async with db_service.get_session() as session:
            upload_repo = FileUploadRepository(session)
            uploads = await upload_repo.get_recent_uploads(limit)
            
            return [
                UploadStatusResponse(
                    upload_id=str(upload.id),
                    filename=upload.filename,
                    file_type=upload.file_type,
                    file_size=upload.file_size,
                    status=upload.status,
                    progress=upload.progress,
                    document_count=upload.document_count,
                    error_message=upload.error_message,
                    created_at=upload.created_at,
                    processed_at=upload.processed_at
                )
                for upload in uploads
            ]
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取上传记录失败: {str(e)}"
        )


@router.get("/uploads/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """
    获取上传处理状态
    
    Args:
        upload_id: 上传记录 ID
        current_user: 当前用户信息
        
    Returns:
        UploadStatusResponse: 上传状态
    """
    try:
        settings = get_settings()
        db_service = DatabaseService(settings.postgres_url)
        
        async with db_service.get_session() as session:
            upload_repo = FileUploadRepository(session)
            upload = await upload_repo.get_upload_by_id(upload_id)
            
            if not upload:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="上传记录不存在"
                )
            
            return UploadStatusResponse(
                upload_id=str(upload.id),
                filename=upload.filename,
                file_type=upload.file_type,
                file_size=upload.file_size,
                status=upload.status,
                progress=upload.progress,
                document_count=upload.document_count,
                error_message=upload.error_message,
                created_at=upload.created_at,
                processed_at=upload.processed_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取上传状态失败: {str(e)}"
        )


@router.post("/uploads/{upload_id}/retry")
async def retry_upload(
    upload_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """
    重试失败的上传
    
    Args:
        upload_id: 上传记录 ID
        current_user: 当前用户信息
        
    Returns:
        dict: 重试结果
    """
    try:
        settings = get_settings()
        db_service = DatabaseService(settings.postgres_url)
        
        processor = FileUploadProcessor(db_service)
        success = await processor.retry_upload(upload_id)
        
        if success:
            return {"message": "重试任务已启动"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="重试失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重试上传失败: {str(e)}"
        )


@router.delete("/uploads/{upload_id}")
async def rollback_upload(
    upload_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """
    回滚上传（删除相关文档）
    
    Args:
        upload_id: 上传记录 ID
        current_user: 当前用户信息
        
    Returns:
        dict: 回滚结果
    """
    try:
        settings = get_settings()
        db_service = DatabaseService(settings.postgres_url)
        
        processor = FileUploadProcessor(db_service)
        success = await processor.rollback_upload(upload_id)
        
        if success:
            return {"message": "回滚成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="回滚失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回滚上传失败: {str(e)}"
        )


@router.post("/preview", response_model=FilePreviewResponse)
async def preview_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_admin_token)
):
    """
    预览文件内容（不保存）
    
    Args:
        file: 上传的文件
        current_user: 当前用户信息
        
    Returns:
        FilePreviewResponse: 文件预览结果
    """
    try:
        from src.services.file_parser import FileParser
        
        # 验证文件
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 检查文件大小
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过限制 (10MB)"
            )
        
        # 解析文件
        parser = FileParser()
        result = await parser.parse_file(file_content, file.filename)
        
        # 估算 token 数量（粗略估算：1 token ≈ 4 字符）
        total_chars = sum(len(chunk) for chunk in result['chunks'])
        estimated_tokens = total_chars // 4
        
        return FilePreviewResponse(
            filename=file.filename,
            file_type=result['metadata']['file_type'],
            chunks=result['chunks'],
            total_chunks=len(result['chunks']),
            estimated_tokens=estimated_tokens
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件预览失败: {str(e)}"
        )


def _detect_file_type(file_content: bytes, filename: str) -> str:
    """检测文件类型"""
    try:
        # 使用 python-magic 检测 MIME 类型
        mime_type = magic.from_buffer(file_content, mime=True)
        
        # 支持的文件类型映射
        supported_types = {
            'application/pdf': 'pdf',
            'text/markdown': 'markdown',
            'text/plain': 'txt',
            'text/x-markdown': 'markdown'
        }
        
        if mime_type in supported_types:
            return supported_types[mime_type]
        
        # 根据文件扩展名判断
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext in ['pdf']:
            return 'pdf'
        elif ext in ['md', 'markdown']:
            return 'markdown'
        elif ext in ['txt', 'text']:
            return 'txt'
        
        # MIME 类型不支持，且扩展名也不支持
        raise ValueError(f"不支持的文件类型: {mime_type}")
        
    except ValueError as e:
        # 重新抛出 ValueError（不支持的文件类型）
        raise e
    except Exception as e:
        # 其他异常（如 magic 检测失败）抛出通用错误
        raise ValueError(f"无法识别文件类型: {filename}")
