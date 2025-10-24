"""
管理员认证模块

提供 JWT token 生成/验证、密码哈希等功能。
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
import hashlib
import secrets

# 临时使用 SHA-256 + 盐值进行密码哈希（生产环境建议使用 bcrypt）
def simple_hash_password(password: str) -> str:
    """简单的密码哈希方法"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def simple_verify_password(password: str, hashed_password: str) -> bool:
    """验证简单哈希密码"""
    try:
        salt, stored_hash = hashed_password.split(":", 1)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == stored_hash
    except:
        return False


class AdminSecurity:
    """管理员安全认证类"""
    
    def __init__(self, secret_key: str, expire_minutes: int = 60):
        """
        初始化安全认证
        
        Args:
            secret_key: JWT 密钥
            expire_minutes: token 过期时间（分钟）
        """
        self.secret_key = secret_key
        self.expire_minutes = expire_minutes
        self.algorithm = "HS256"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否正确
        """
        return simple_verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希密码
        """
        return simple_hash_password(password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码的数据
            
        Returns:
            str: JWT token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌
        
        Args:
            token: JWT token
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的数据，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        创建刷新令牌（有效期更长）
        
        Args:
            data: 要编码的数据
            
        Returns:
            str: 刷新 token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7天有效期
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证刷新令牌
        
        Args:
            token: 刷新 token
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的数据，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                return None
            return payload
        except JWTError:
            return None
