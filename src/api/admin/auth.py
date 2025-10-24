"""
管理员认证 API

提供登录、刷新 token 等认证接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.core.admin_security_bcrypt import AdminSecurity
from src.core.config import get_settings
from src.api.admin.dependencies import get_admin_security
from src.db.base import DatabaseService
from src.db.models import AdminUser

router = APIRouter(prefix="/api/admin/auth", tags=["Admin Auth"])


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """刷新 token 请求"""
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    admin_security: AdminSecurity = Depends(get_admin_security)
):
    """
    管理员登录
    
    Args:
        request: 登录请求
        admin_security: 管理员安全认证实例
        
    Returns:
        LoginResponse: 登录响应
        
    Raises:
        HTTPException: 用户名或密码错误时抛出 401 错误
    """
    settings = get_settings()
    
    # 从数据库查询管理员账户
    db_service = DatabaseService(settings.postgres_url)
    try:
        async with db_service.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == request.username)
            )
            admin_user = result.scalar_one_or_none()
            
            # 验证用户存在且账户状态为激活（'Y'）
            if not admin_user or admin_user.is_active != "Y":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 验证密码
            if not admin_security.verify_password(request.password, admin_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    finally:
        # 确保数据库引擎被正确释放，避免连接泄漏
        await db_service.engine.dispose()
    
    # 生成访问令牌和刷新令牌
    token_data = {
        "sub": request.username,
        "type": "access"
    }
    access_token = admin_security.create_access_token(token_data)
    
    # 生成刷新令牌
    refresh_token_data = {
        "sub": request.username,
        "type": "refresh"
    }
    refresh_token = admin_security.create_refresh_token(refresh_token_data)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60  # 转换为秒
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshRequest,
    admin_security: AdminSecurity = Depends(get_admin_security)
):
    """
    刷新访问令牌
    
    Args:
        request: 刷新请求
        admin_security: 管理员安全认证实例
        
    Returns:
        LoginResponse: 新的访问令牌
        
    Raises:
        HTTPException: 刷新令牌无效时抛出 401 错误
    """
    # 验证刷新令牌
    payload = admin_security.verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成新的访问令牌
    token_data = {
        "sub": payload.get("sub"),
        "type": "access"
    }
    access_token = admin_security.create_access_token(token_data)
    
    settings = get_settings()
    return LoginResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 保持原有的刷新令牌
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60
    )
