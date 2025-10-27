"""
管理员认证模块简化测试（跳过 bcrypt 相关测试）
"""

from datetime import datetime

from src.core.admin_security_bcrypt import AdminSecurity


class TestAdminSecuritySimple:
    """管理员认证简化测试类"""

    def setup_method(self):
        """测试前准备"""
        self.secret_key = "test-secret-key-min-32-chars-long"
        self.expire_minutes = 60
        self.security = AdminSecurity(self.secret_key, self.expire_minutes)

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
        token = self.security.create_access_token(data)
        payload = self.security.verify_token(token)

        # 应该包含过期时间
        assert "exp" in payload

        # 过期时间应该是未来时间
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.now()
        assert exp_time > now

    def test_security_initialization(self):
        """测试安全模块初始化"""
        assert self.security.secret_key == self.secret_key
        assert self.security.expire_minutes == self.expire_minutes
        assert self.security.algorithm == "HS256"

    def test_different_secret_keys(self):
        """测试不同密钥产生不同 token"""
        security1 = AdminSecurity("key1", 60)
        security2 = AdminSecurity("key2", 60)

        data = {"username": "admin"}
        token1 = security1.create_access_token(data)
        token2 = security2.create_access_token(data)

        # 不同密钥应该产生不同 token
        assert token1 != token2

        # 每个 token 只能被对应密钥验证
        assert security1.verify_token(token1) is not None
        assert security1.verify_token(token2) is None
        assert security2.verify_token(token1) is None
        assert security2.verify_token(token2) is not None
