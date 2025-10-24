"""
管理 API 依赖

提供 JWT 认证依赖和其他通用依赖。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.admin_security_bcrypt import AdminSecurity
from src.core.config import get_settings

# HTTP Bearer 认证方案
security_scheme = HTTPBearer()


async def get_admin_security() -> AdminSecurity:
    """获取管理员安全认证实例"""
    settings = get_settings()
    return AdminSecurity(
        secret_key=settings.jwt_secret_key,
        expire_minutes=settings.jwt_expire_minutes
    )


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    admin_security: AdminSecurity = Depends(get_admin_security)
) -> dict:
    """
    验证管理员 JWT token
    
    Args:
        credentials: HTTP Bearer 认证凭据
        admin_security: 管理员安全认证实例
        
    Returns:
        dict: 解码后的 token 数据
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    token = credentials.credentials
    payload = admin_security.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload
