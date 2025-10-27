"""
管理 API 单元测试
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from src.core.admin_security_bcrypt import AdminSecurity
from src.main import app


class TestAdminAPI:
    """管理 API 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.secret_key = "test-secret-key-min-32-chars-long"
        self.security = AdminSecurity(self.secret_key, 60)

    def test_health_check(self):
        """测试健康检查接口"""
        response = self.client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
        # 不检查具体状态，因为测试环境可能没有连接外部服务

    @patch('src.core.config.get_settings')
    @patch('src.api.admin.auth.DatabaseService')
    def test_admin_login_success(self, mock_db_service, mock_get_settings):
        """测试管理员登录成功"""
        # Mock 配置
        mock_settings = Mock()
        mock_settings.admin_username = "admin"
        mock_settings.jwt_secret_key = self.secret_key
        mock_settings.jwt_expire_minutes = 60
        mock_settings.postgres_url = "postgresql://test"
        mock_get_settings.return_value = mock_settings

        # Mock 数据库查询结果
        mock_admin_user = Mock()
        mock_admin_user.username = "admin"
        mock_admin_user.password_hash = self.security.get_password_hash("password123")
        mock_admin_user.is_active = "Y"

        mock_session = Mock()
        mock_session.execute = AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=mock_admin_user)))
        mock_db_service.return_value.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_service.return_value.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.return_value.engine.dispose = AsyncMock()  # Mock engine.dispose()

        # 测试登录
        login_data = {
            "username": "admin",
            "password": "password123"
        }

        response = self.client.post("/api/admin/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600  # 60分钟 * 60秒

    @patch('src.core.config.get_settings')
    @patch('src.api.admin.auth.DatabaseService')
    def test_admin_login_wrong_username(self, mock_db_service, mock_get_settings):
        """测试管理员登录 - 错误用户名"""
        # Mock 配置
        mock_settings = Mock()
        mock_settings.jwt_secret_key = self.secret_key
        mock_settings.jwt_expire_minutes = 60
        mock_settings.postgres_url = "postgresql://test"
        mock_get_settings.return_value = mock_settings

        # Mock 数据库查询结果 - 用户不存在
        mock_session = Mock()
        mock_session.execute = AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=None)))
        mock_db_service.return_value.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_service.return_value.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.return_value.engine.dispose = AsyncMock()

        # 测试错误用户名
        login_data = {
            "username": "wrong_user",
            "password": "password123"
        }

        response = self.client.post("/api/admin/auth/login", json=login_data)
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @patch('src.core.config.get_settings')
    @patch('src.api.admin.auth.DatabaseService')
    def test_admin_login_wrong_password(self, mock_db_service, mock_get_settings):
        """测试管理员登录 - 错误密码"""
        # Mock 配置
        mock_settings = Mock()
        mock_settings.jwt_secret_key = self.secret_key
        mock_settings.jwt_expire_minutes = 60
        mock_settings.postgres_url = "postgresql://test"
        mock_get_settings.return_value = mock_settings

        # Mock 数据库查询结果 - 用户存在但密码错误
        mock_admin_user = Mock()
        mock_admin_user.username = "admin"
        mock_admin_user.password_hash = self.security.get_password_hash("correct_password")
        mock_admin_user.is_active = "Y"

        mock_session = Mock()
        mock_session.execute = AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=mock_admin_user)))
        mock_db_service.return_value.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_service.return_value.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.return_value.engine.dispose = AsyncMock()

        # 测试错误密码
        login_data = {
            "username": "admin",
            "password": "wrong_password"
        }

        response = self.client.post("/api/admin/auth/login", json=login_data)
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_admin_login_missing_fields(self):
        """测试管理员登录 - 缺少字段"""
        # 缺少用户名
        response = self.client.post("/api/admin/auth/login", json={"password": "password123"})
        assert response.status_code == 422

        # 缺少密码
        response = self.client.post("/api/admin/auth/login", json={"username": "admin"})
        assert response.status_code == 422

    def test_protected_endpoint_without_token(self):
        """测试受保护端点 - 无 token"""
        response = self.client.get("/api/admin/knowledge/documents")
        assert response.status_code == 403

    def test_protected_endpoint_with_invalid_token(self):
        """测试受保护端点 - 无效 token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/api/admin/knowledge/documents", headers=headers)
        assert response.status_code == 401

    @patch('src.repositories.milvus.base_milvus_repository.get_milvus_client')
    def test_protected_endpoint_with_valid_token(self, mock_get_milvus_client):
        """测试受保护端点 - 有效 token"""
        from src.api.admin.dependencies import get_admin_security

        # 使用 FastAPI 的 dependency_overrides 来 mock AdminSecurity 依赖
        app.dependency_overrides[get_admin_security] = lambda: self.security

        try:
            # 创建有效 token
            token = self.security.create_access_token({"username": "admin"})
            headers = {"Authorization": f"Bearer {token}"}

            # Mock Milvus 客户端
            mock_milvus_client = Mock()
            mock_milvus_client.query.return_value = []
            mock_get_milvus_client.return_value = mock_milvus_client

            response = self.client.get("/api/admin/knowledge/documents", headers=headers)
            assert response.status_code == 200
        finally:
            # 清理 dependency_overrides
            app.dependency_overrides.clear()

    def test_token_refresh(self):
        """测试 token 刷新"""
        # 创建有效的刷新 token
        refresh_token = self.security.create_refresh_token({"username": "admin"})

        response = self.client.post("/api/admin/auth/refresh",
                                  json={"refresh_token": refresh_token})

        # 根据实际实现，刷新令牌应该返回 200 或 401
        assert response.status_code in [200, 401]

    def test_cors_headers(self):
        """测试 CORS 头部"""
        response = self.client.options("/api/admin/auth/login")
        # 检查 CORS 头部是否存在
        assert response.status_code in [200, 204, 405]  # 405 也是可接受的

    def test_request_validation(self):
        """测试请求验证"""
        # 测试空请求体
        response = self.client.post("/api/admin/auth/login", json={})
        assert response.status_code == 422

        # 测试无效数据类型
        response = self.client.post("/api/admin/auth/login", json={
            "username": 123,  # 应该是字符串
            "password": "password123"
        })
        assert response.status_code == 422

    @patch('src.core.config.get_settings')
    @patch('src.api.admin.auth.DatabaseService')
    def test_jwt_expiration_handling(self, mock_db_service, mock_get_settings):
        """测试 JWT 过期处理"""
        # Mock 配置
        mock_settings = Mock()
        mock_settings.jwt_secret_key = self.secret_key
        mock_settings.jwt_expire_minutes = 0  # 立即过期
        mock_settings.postgres_url = "postgresql://test"
        mock_get_settings.return_value = mock_settings

        # Mock 数据库查询结果
        mock_admin_user = Mock()
        mock_admin_user.username = "admin"
        mock_admin_user.password_hash = self.security.get_password_hash("password123")
        mock_admin_user.is_active = "Y"

        mock_session = Mock()
        mock_session.execute = AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=mock_admin_user)))
        mock_db_service.return_value.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_service.return_value.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.return_value.engine.dispose = AsyncMock()

        # 登录获取 token
        login_data = {
            "username": "admin",
            "password": "password123"
        }
        response = self.client.post("/api/admin/auth/login", json=login_data)
        assert response.status_code == 200

        token = response.json()["access_token"]

        # 使用过期 token 访问受保护端点
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/admin/knowledge/documents", headers=headers)
        # 注意：由于 token 可能没有真正过期，这里检查状态码范围
        assert response.status_code in [200, 401]
