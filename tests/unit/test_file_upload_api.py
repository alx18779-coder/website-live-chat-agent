"""
文件上传 API 单元测试
"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO

from src.main import app
from src.api.admin.knowledge import router
from src.core.config import get_settings


class TestFileUploadAPI:
    """文件上传 API 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.settings = get_settings()
        
        # 使用 dependency_overrides 来 mock 认证
        from src.api.admin.dependencies import verify_admin_token
        
        def mock_verify_admin_token():
            return {"sub": "admin"}
        
        app.dependency_overrides[verify_admin_token] = mock_verify_admin_token
    
    def teardown_method(self):
        """测试后清理"""
        # 清理依赖覆盖
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def mock_admin_token(self):
        """模拟管理员 token"""
        return "mock-admin-token"
    
    @pytest.fixture
    def mock_upload_file(self):
        """模拟上传文件"""
        content = b"Sample file content"
        return UploadFile(
            file=BytesIO(content),
            filename="test.txt",
            size=len(content)
        )
    
    @pytest.fixture
    def mock_pdf_file(self):
        """模拟 PDF 文件"""
        content = b"PDF content"
        return UploadFile(
            file=BytesIO(content),
            filename="test.pdf",
            size=len(content)
        )
    
    def test_upload_files_success(self, mock_admin_token, mock_upload_file):
        """测试文件上传成功"""
        with patch('src.api.admin.knowledge.verify_admin_token', return_value={"sub": "admin"}) as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor, \
             patch('src.api.admin.knowledge._detect_file_type', return_value='txt'), \
             patch('src.api.admin.knowledge.magic.from_buffer', return_value='text/plain'):
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录创建
            mock_upload_record = MagicMock()
            mock_upload_record.id = "test-upload-id"
            mock_repo.return_value.create_upload_record.return_value = mock_upload_record
            
            # 执行上传
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files={"files": ("test.txt", mock_upload_file.file, "text/plain")},
                data={"source": "test", "version": "1.0"},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["filename"] == "test.txt"
            assert data[0]["status"] == "pending"
    
    def test_upload_files_size_limit(self, mock_admin_token):
        """测试文件大小限制"""
        # 创建超过限制的文件
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # 超过 10MB
        large_file = UploadFile(
            file=BytesIO(large_content),
            filename="large.txt",
            size=len(large_content)
        )
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify:
            mock_verify.return_value = {"sub": "admin"}
            
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files={"files": ("large.txt", large_file.file, "text/plain")},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "failed"
            assert "文件大小超过限制" in data[0]["message"]
    
    def test_upload_files_invalid_type(self, mock_admin_token):
        """测试不支持的文件类型"""
        content = b"Some content"
        invalid_file = UploadFile(
            file=BytesIO(content),
            filename="test.exe",
            size=len(content)
        )
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge._detect_file_type', side_effect=ValueError("不支持的文件类型")):
            
            mock_verify.return_value = {"sub": "admin"}
            
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files={"files": ("test.exe", invalid_file.file, "application/octet-stream")},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "failed"
            assert "不支持的文件类型" in data[0]["message"]
    
    def test_get_upload_records_success(self, mock_admin_token):
        """测试获取上传记录成功"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录
            mock_upload = MagicMock()
            mock_upload.id = "test-id"
            mock_upload.filename = "test.txt"
            mock_upload.file_type = "txt"
            mock_upload.file_size = 100
            mock_upload.status = "completed"
            mock_upload.progress = 100
            mock_upload.document_count = 5
            mock_upload.error_message = None
            mock_upload.created_at = "2023-01-01T00:00:00"
            mock_upload.processed_at = "2023-01-01T00:01:00"
            
            mock_repo.return_value.get_recent_uploads.return_value = [mock_upload]
            
            # 执行请求
            response = self.client.get(
                "/api/admin/knowledge/uploads",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["upload_id"] == "test-id"
            assert data[0]["filename"] == "test.txt"
            assert data[0]["status"] == "completed"
    
    def test_get_upload_status_success(self, mock_admin_token):
        """测试获取上传状态成功"""
        upload_id = "test-upload-id"
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录
            mock_upload = MagicMock()
            mock_upload.id = upload_id
            mock_upload.filename = "test.txt"
            mock_upload.file_type = "txt"
            mock_upload.file_size = 100
            mock_upload.status = "processing"
            mock_upload.progress = 50
            mock_upload.document_count = 0
            mock_upload.error_message = None
            mock_upload.created_at = "2023-01-01T00:00:00"
            mock_upload.processed_at = None
            
            mock_repo.return_value.get_upload_by_id.return_value = mock_upload
            
            # 执行请求
            response = self.client.get(
                f"/api/admin/knowledge/uploads/{upload_id}",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["upload_id"] == upload_id
            assert data["status"] == "processing"
            assert data["progress"] == 50
    
    def test_get_upload_status_not_found(self, mock_admin_token):
        """测试获取不存在的上传状态"""
        upload_id = "non-existent-id"
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟找不到记录
            mock_repo.return_value.get_upload_by_id.return_value = None
            
            # 执行请求
            response = self.client.get(
                f"/api/admin/knowledge/uploads/{upload_id}",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 404
            assert "上传记录不存在" in response.json()["detail"]
    
    def test_retry_upload_success(self, mock_admin_token):
        """测试重试上传成功"""
        upload_id = "test-upload-id"
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_db_service.return_value = MagicMock()
            
            # 模拟处理器
            mock_processor.return_value.retry_upload.return_value = True
            
            # 执行请求
            response = self.client.post(
                f"/api/admin/knowledge/uploads/{upload_id}/retry",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            assert "重试任务已启动" in response.json()["message"]
    
    def test_rollback_upload_success(self, mock_admin_token):
        """测试回滚上传成功"""
        upload_id = "test-upload-id"
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_db_service.return_value = MagicMock()
            
            # 模拟处理器
            mock_processor.return_value.rollback_upload.return_value = True
            
            # 执行请求
            response = self.client.delete(
                f"/api/admin/knowledge/uploads/{upload_id}",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            assert "回滚成功" in response.json()["message"]
    
    def test_preview_file_success(self, mock_admin_token, mock_upload_file):
        """测试文件预览成功"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.FileParser') as mock_parser:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟文件解析器
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_file.return_value = {
                'chunks': ['chunk1', 'chunk2'],
                'metadata': {'file_type': 'txt'}
            }
            mock_parser.return_value = mock_parser_instance
            
            # 执行请求
            response = self.client.post(
                "/api/admin/knowledge/preview",
                files={"file": ("test.txt", mock_upload_file.file, "text/plain")},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test.txt"
            assert data["file_type"] == "txt"
            assert len(data["chunks"]) == 2
            assert data["total_chunks"] == 2
    
    def test_preview_file_size_limit(self, mock_admin_token):
        """测试文件预览大小限制"""
        # 创建超过限制的文件
        large_content = b"x" * (10 * 1024 * 1024 + 1)
        large_file = UploadFile(
            file=BytesIO(large_content),
            filename="large.txt",
            size=len(large_content)
        )
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify:
            mock_verify.return_value = {"sub": "admin"}
            
            response = self.client.post(
                "/api/admin/knowledge/preview",
                files={"file": ("large.txt", large_file.file, "text/plain")},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            # 验证响应
            assert response.status_code == 400
            assert "文件大小超过限制" in response.json()["detail"]
    
    def test_detect_file_type_pdf(self):
        """测试 PDF 文件类型检测"""
        from src.api.admin.knowledge import _detect_file_type
        
        pdf_content = b"PDF content"
        
        with patch('src.api.admin.knowledge.magic') as mock_magic:
            mock_magic.from_buffer.return_value = 'application/pdf'
            
            result = _detect_file_type(pdf_content, "test.pdf")
            
            assert result == "pdf"
    
    def test_detect_file_type_markdown(self):
        """测试 Markdown 文件类型检测"""
        from src.api.admin.knowledge import _detect_file_type
        
        md_content = b"# Markdown content"
        
        with patch('src.api.admin.knowledge.magic') as mock_magic:
            mock_magic.from_buffer.return_value = 'text/markdown'
            
            result = _detect_file_type(md_content, "test.md")
            
            assert result == "markdown"
    
    def test_detect_file_type_by_extension(self):
        """测试通过扩展名检测文件类型"""
        from src.api.admin.knowledge import _detect_file_type
        
        content = b"Some content"
        
        with patch('src.api.admin.knowledge.magic') as mock_magic:
            mock_magic.from_buffer.return_value = 'unknown/type'
            
            # 测试各种扩展名
            assert _detect_file_type(content, "test.pdf") == "pdf"
            assert _detect_file_type(content, "test.md") == "markdown"
            assert _detect_file_type(content, "test.txt") == "txt"
    
    def test_detect_file_type_unsupported(self):
        """测试不支持的文件类型"""
        from src.api.admin.knowledge import _detect_file_type
        
        content = b"Some content"
        
        with patch('src.api.admin.knowledge.magic') as mock_magic:
            mock_magic.from_buffer.return_value = 'application/unsupported'
            
            with pytest.raises(ValueError, match="不支持的文件类型"):
                _detect_file_type(content, "test.xyz")
