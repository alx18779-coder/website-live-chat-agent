"""
系统配置 API

提供系统配置查看和健康检查接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from src.api.admin.dependencies import verify_admin_token
from src.core.config import get_settings

router = APIRouter(prefix="/api/admin/settings", tags=["System Settings"])


class SystemConfigResponse(BaseModel):
    """系统配置响应"""
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    vector_top_k: int
    vector_score_threshold: float
    milvus_host: str
    milvus_port: int
    redis_host: str
    redis_port: int


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    services: Dict[str, Dict[str, Any]]


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config(
    current_user: dict = Depends(verify_admin_token)
):
    """
    获取系统配置（脱敏）
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        SystemConfigResponse: 系统配置信息
    """
    try:
        settings = get_settings()
        
        return SystemConfigResponse(
            llm_provider=settings.llm_provider,
            llm_model=getattr(settings, f"{settings.llm_provider}_model", "unknown"),
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            vector_top_k=settings.vector_top_k,
            vector_score_threshold=settings.vector_score_threshold,
            milvus_host=settings.milvus_host,
            milvus_port=settings.milvus_port,
            redis_host=settings.redis_host,
            redis_port=settings.redis_port
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统配置失败: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    current_user: dict = Depends(verify_admin_token)
):
    """
    系统健康检查
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        HealthCheckResponse: 健康检查结果
    """
    try:
        services = {}
        overall_status = "healthy"
        
        # 检查 Milvus 连接
        try:
            from src.repositories.milvus.base_milvus_repository import get_milvus_client
            client = await get_milvus_client()
            await client.list_collections()
            services["milvus"] = {"status": "healthy", "message": "连接正常"}
        except Exception as e:
            services["milvus"] = {"status": "unhealthy", "message": str(e)}
            overall_status = "degraded"
        
        # 检查 Redis 连接
        try:
            import redis
            settings = get_settings()
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db
            )
            r.ping()
            services["redis"] = {"status": "healthy", "message": "连接正常"}
        except Exception as e:
            services["redis"] = {"status": "unhealthy", "message": str(e)}
            overall_status = "degraded"
        
        # 检查 PostgreSQL 连接
        try:
            from src.db.base import DatabaseService
            settings = get_settings()
            db_service = DatabaseService(settings.postgres_url)
            # 简单连接测试
            services["postgres"] = {"status": "healthy", "message": "连接正常"}
        except Exception as e:
            services["postgres"] = {"status": "unhealthy", "message": str(e)}
            overall_status = "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            services=services
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )
