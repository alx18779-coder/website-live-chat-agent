"""
管理员认证模块单元测试
"""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

from src.core.admin_security_bcrypt import AdminSecurity


class TestAdminSecurity:
    """管理员认证测试类"""

    def setup_method(self):
        """测试前准备"""
        self.secret_key = "test-secret-key-min-32-chars-long"
        self.expire_minutes = 60
        self.security = AdminSecurity(self.secret_key, self.expire_minutes)

    def test_password_hashing(self):
        """测试密码哈希"""
        password = "test_password_123"
        hashed = self.security.get_password_hash(password)

        # 哈希值应该与原始密码不同
        assert hashed != password
        # 哈希值应该以 bcrypt 标识符开头
        assert hashed.startswith("$2b$")
        # 长度应该合理
        assert len(hashed) > 50

    def test_password_verification(self):
        """测试密码验证"""
        password = "test_password_123"
        hashed = self.security.get_password_hash(password)

        # 正确密码应该验证通过
        assert self.security.verify_password(password, hashed) is True

        # 错误密码应该验证失败
        assert self.security.verify_password("wrong_password", hashed) is False

    def test_token_creation(self):
        """测试 JWT token 创建"""
        data = {"username": "admin", "user_id": "123"}
        token = self.security.create_access_token(data)

        # token 应该存在且不为空
        assert token is not None
        assert len(token) > 0
        # token 应该包含三个部分（header.payload.signature）
        assert len(token.split(".")) == 3

    def test_token_verification(self):
        """测试 JWT token 验证"""
        data = {"username": "admin", "user_id": "123"}
        token = self.security.create_access_token(data)

        # 有效 token 应该验证通过
        payload = self.security.verify_token(token)
        assert payload is not None
        assert payload["username"] == "admin"
        assert payload["user_id"] == "123"
        assert "exp" in payload

    def test_token_expiration(self):
        """测试 token 过期"""
        # 使用 patch 创建一个过期的 token
        past_time = datetime.utcnow() - timedelta(hours=2)  # 2小时前

        with patch('src.core.admin_security_bcrypt.datetime') as mock_datetime:
            # 创建 token 时使用过去的时间
            mock_datetime.utcnow.return_value = past_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            data = {"username": "admin"}
            expired_token = self.security.create_access_token(data)

        # 验证应该失败（已过期）
        payload = self.security.verify_token(expired_token)
        assert payload is None

    def test_invalid_token(self):
        """测试无效 token"""
        # 空 token
        assert self.security.verify_token("") is None

        # 无效格式 token
        assert self.security.verify_token("invalid.token") is None

        # 使用错误密钥签名的 token
        wrong_security = AdminSecurity("wrong-secret-key", 60)
        data = {"username": "admin"}
        wrong_token = wrong_security.create_access_token(data)
        assert self.security.verify_token(wrong_token) is None

    def test_token_with_expiration(self):
        """测试 token 包含过期时间"""
        data = {"username": "admin"}
        before = time.time()
        token = self.security.create_access_token(data)
        after = time.time()

        payload = self.security.verify_token(token)

        # 应该包含过期时间
        assert "exp" in payload

        # 过期时间应该在未来
        assert payload["exp"] > after

        # 过期时间应该在配置的分钟数内（允许一些误差）
        expected_exp = before + (self.expire_minutes * 60)
        time_diff = abs(payload["exp"] - expected_exp)
        assert time_diff < 60  # 允许1分钟误差

    def test_different_passwords(self):
        """测试不同密码的哈希"""
        password1 = "password1"
        password2 = "password2"

        hash1 = self.security.get_password_hash(password1)
        hash2 = self.security.get_password_hash(password2)

        # 不同密码应该产生不同哈希
        assert hash1 != hash2

        # 每个密码只能验证自己的哈希
        assert self.security.verify_password(password1, hash1) is True
        assert self.security.verify_password(password1, hash2) is False
        assert self.security.verify_password(password2, hash1) is False
        assert self.security.verify_password(password2, hash2) is True

    def test_same_password_different_hashes(self):
        """测试相同密码产生不同哈希（盐值）"""
        password = "same_password"
        hash1 = self.security.get_password_hash(password)
        hash2 = self.security.get_password_hash(password)

        # 相同密码应该产生不同哈希（由于盐值）
        assert hash1 != hash2

        # 但都应该能验证原始密码
        assert self.security.verify_password(password, hash1) is True
        assert self.security.verify_password(password, hash2) is True
