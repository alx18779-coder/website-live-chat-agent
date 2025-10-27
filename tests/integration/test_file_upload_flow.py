"""
文件上传完整流程集成测试
"""

import pytest
import tempfile
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from io import BytesIO

from src.main import app
from src.core.config import get_settings
from src.db.base import DatabaseService
from src.services.file_upload_processor import FileUploadProcessor
from src.services.file_parser import FileParser


class TestFileUploadFlow:
    """文件上传流程集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.settings = get_settings()
    
    @pytest.fixture
    def mock_admin_token(self):
        """模拟管理员 token"""
        return "mock-admin-token"
    
    @pytest.fixture
    def sample_pdf_content(self):
        """示例 PDF 内容"""
        return b"Sample PDF content for testing"
    
    @pytest.fixture
    def sample_markdown_content(self):
        """示例 Markdown 内容"""
        return b"# Test Document\n\nThis is a **test** markdown document.\n\n## Section 1\n\nSome content here."
    
    @pytest.fixture
    def sample_text_content(self):
        """示例文本内容"""
        return b"This is a simple text file for testing purposes."
    
    @pytest.mark.asyncio
    async def test_complete_upload_flow_pdf(self, mock_admin_token, sample_pdf_content):
        """测试完整的 PDF 上传流程"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor, \
             patch('src.api.admin.knowledge._detect_file_type', return_value='pdf'):
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录
            mock_upload_record = MagicMock()
            mock_upload_record.id = "test-upload-id"
            mock_upload_record.filename = "test.pdf"
            mock_upload_record.file_type = "pdf"
            mock_upload_record.file_size = len(sample_pdf_content)
            mock_upload_record.file_path = "/tmp/test.pdf"
            mock_upload_record.source = "test"
            mock_upload_record.version = "1.0"
            mock_upload_record.uploader = "admin"
            mock_upload_record.status = "pending"
            mock_upload_record.progress = 0
            mock_upload_record.document_count = 0
            mock_upload_record.milvus_ids = []
            mock_upload_record.error_message = None
            mock_upload_record.created_at = "2023-01-01T00:00:00"
            mock_upload_record.processed_at = None
            
            mock_repo.return_value.create_upload_record.return_value = mock_upload_record
            mock_repo.return_value.get_upload_by_id.return_value = mock_upload_record
            
            # 1. 测试文件上传
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files={"files": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")},
                data={"source": "test", "version": "1.0"},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            upload_data = response.json()
            assert len(upload_data) == 1
            assert upload_data[0]["filename"] == "test.pdf"
            assert upload_data[0]["status"] == "pending"
            
            # 2. 测试获取上传状态
            response = self.client.get(
                f"/api/admin/knowledge/uploads/{mock_upload_record.id}",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["upload_id"] == str(mock_upload_record.id)
            assert status_data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_complete_upload_flow_markdown(self, mock_admin_token, sample_markdown_content):
        """测试完整的 Markdown 上传流程"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor, \
             patch('src.api.admin.knowledge._detect_file_type', return_value='markdown'):
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录
            mock_upload_record = MagicMock()
            mock_upload_record.id = "test-upload-id"
            mock_upload_record.filename = "test.md"
            mock_upload_record.file_type = "markdown"
            mock_upload_record.file_size = len(sample_markdown_content)
            mock_upload_record.file_path = "/tmp/test.md"
            mock_upload_record.source = "test"
            mock_upload_record.version = "1.0"
            mock_upload_record.uploader = "admin"
            mock_upload_record.status = "pending"
            mock_upload_record.progress = 0
            mock_upload_record.document_count = 0
            mock_upload_record.milvus_ids = []
            mock_upload_record.error_message = None
            mock_upload_record.created_at = "2023-01-01T00:00:00"
            mock_upload_record.processed_at = None
            
            mock_repo.return_value.create_upload_record.return_value = mock_upload_record
            mock_repo.return_value.get_upload_by_id.return_value = mock_upload_record
            
            # 1. 测试文件上传
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files={"files": ("test.md", BytesIO(sample_markdown_content), "text/markdown")},
                data={"source": "test", "version": "1.0"},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            upload_data = response.json()
            assert len(upload_data) == 1
            assert upload_data[0]["filename"] == "test.md"
            assert upload_data[0]["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_file_preview_flow(self, mock_admin_token, sample_text_content):
        """测试文件预览流程"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.FileParser') as mock_parser:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟文件解析器
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_file.return_value = {
                'chunks': [
                    'This is a simple text file for testing purposes.',
                    'This is another chunk of text.'
                ],
                'metadata': {
                    'file_type': 'txt',
                    'filename': 'test.txt',
                    'file_size': len(sample_text_content),
                    'total_chunks': 2,
                    'total_chars': 100
                }
            }
            mock_parser.return_value = mock_parser_instance
            
            # 测试文件预览
            response = self.client.post(
                "/api/admin/knowledge/preview",
                files={"file": ("test.txt", BytesIO(sample_text_content), "text/plain")},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            preview_data = response.json()
            assert preview_data["filename"] == "test.txt"
            assert preview_data["file_type"] == "txt"
            assert len(preview_data["chunks"]) == 2
            assert preview_data["total_chunks"] == 2
            assert preview_data["estimated_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_upload_retry_flow(self, mock_admin_token):
        """测试上传重试流程"""
        upload_id = "test-upload-id"
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_db_service.return_value = MagicMock()
            
            # 模拟处理器重试成功
            mock_processor.return_value.retry_upload.return_value = True
            
            # 测试重试上传
            response = self.client.post(
                f"/api/admin/knowledge/uploads/{upload_id}/retry",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            assert "重试任务已启动" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_upload_rollback_flow(self, mock_admin_token):
        """测试上传回滚流程"""
        upload_id = "test-upload-id"
        
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor:
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_db_service.return_value = MagicMock()
            
            # 模拟处理器回滚成功
            mock_processor.return_value.rollback_upload.return_value = True
            
            # 测试回滚上传
            response = self.client.delete(
                f"/api/admin/knowledge/uploads/{upload_id}",
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            assert "回滚成功" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_file_parser_integration(self, sample_pdf_content, sample_markdown_content, sample_text_content):
        """测试文件解析器集成"""
        parser = FileParser()
        
        # 测试 PDF 解析
        with patch('src.services.file_parser.PdfReader') as mock_pdf_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            
            mock_reader_instance = MagicMock()
            mock_reader_instance.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader_instance
            
            result = await parser.parse_file(sample_pdf_content, "test.pdf")
            
            assert 'chunks' in result
            assert 'metadata' in result
            assert 'raw_content' in result
            assert result['metadata']['file_type'] == 'pdf'
            assert result['metadata']['filename'] == 'test.pdf'
        
        # 测试 Markdown 解析
        result = await parser.parse_file(sample_markdown_content, "test.md")
        
        assert 'chunks' in result
        assert 'metadata' in result
        assert result['metadata']['file_type'] == 'markdown'
        assert len(result['chunks']) > 0
        
        # 测试文本解析
        result = await parser.parse_file(sample_text_content, "test.txt")
        
        assert 'chunks' in result
        assert 'metadata' in result
        assert result['metadata']['file_type'] == 'txt'
        assert len(result['chunks']) > 0
    
    @pytest.mark.asyncio
    async def test_upload_processor_integration(self):
        """测试文件上传处理器集成"""
        with patch('src.services.file_upload_processor.DatabaseService') as mock_db_service, \
             patch('src.services.file_upload_processor.FileUploadRepository') as mock_repo, \
             patch('src.services.file_upload_processor.get_milvus_client') as mock_milvus, \
             patch('src.services.file_upload_processor.KnowledgeRepository') as mock_knowledge_repo, \
             patch('src.services.file_upload_processor.get_embedding_service') as mock_embedding:
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录
            mock_upload_record = MagicMock()
            mock_upload_record.id = "test-upload-id"
            mock_upload_record.filename = "test.txt"
            mock_upload_record.file_type = "txt"
            mock_upload_record.file_size = 100
            mock_upload_record.file_path = "/tmp/test.txt"
            mock_upload_record.source = "test"
            mock_upload_record.version = "1.0"
            mock_upload_record.uploader = "admin"
            mock_upload_record.status = "pending"
            mock_upload_record.progress = 0
            mock_upload_record.document_count = 0
            mock_upload_record.milvus_ids = []
            mock_upload_record.error_message = None
            mock_upload_record.created_at = "2023-01-01T00:00:00"
            mock_upload_record.processed_at = None
            
            mock_repo.return_value.get_upload_by_id.return_value = mock_upload_record
            mock_repo.return_value.update_status.return_value = True
            mock_repo.return_value.update_result.return_value = True
            
            # 模拟 Milvus 客户端
            mock_milvus_client = AsyncMock()
            mock_milvus.return_value = mock_milvus_client
            
            # 模拟知识库仓库
            mock_knowledge_repo_instance = AsyncMock()
            mock_knowledge_repo.return_value = mock_knowledge_repo_instance
            mock_knowledge_repo_instance.add_document.return_value = "doc-id-1"
            
            # 模拟嵌入服务
            mock_embedding_service = AsyncMock()
            mock_embedding_service.get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_embedding.return_value = mock_embedding_service
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write("Sample text content for testing")
                temp_file_path = temp_file.name
            
            try:
                # 更新上传记录的文件路径
                mock_upload_record.file_path = temp_file_path
                
                # 创建处理器
                processor = FileUploadProcessor(mock_db_service.return_value)
                
                # 执行处理
                result = await processor.process_file("test-upload-id")
                
                # 验证结果
                assert result is True
                
                # 验证调用
                mock_repo.return_value.update_status.assert_called()
                mock_repo.return_value.update_result.assert_called()
                mock_knowledge_repo_instance.add_document.assert_called()
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_error_handling_flow(self, mock_admin_token):
        """测试错误处理流程"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor, \
             patch('src.api.admin.knowledge._detect_file_type', side_effect=ValueError("不支持的文件类型")):
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 测试不支持的文件类型
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files={"files": ("test.exe", BytesIO(b"executable content"), "application/octet-stream")},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            upload_data = response.json()
            assert len(upload_data) == 1
            assert upload_data[0]["status"] == "failed"
            assert "不支持的文件类型" in upload_data[0]["message"]
    
    @pytest.mark.asyncio
    async def test_multiple_file_upload(self, mock_admin_token, sample_text_content):
        """测试多文件上传"""
        with patch('src.api.admin.knowledge.verify_admin_token') as mock_verify, \
             patch('src.api.admin.knowledge.DatabaseService') as mock_db_service, \
             patch('src.api.admin.knowledge.FileUploadRepository') as mock_repo, \
             patch('src.api.admin.knowledge.FileUploadProcessor') as mock_processor, \
             patch('src.api.admin.knowledge._detect_file_type', return_value='txt'):
            
            # 模拟认证
            mock_verify.return_value = {"sub": "admin"}
            
            # 模拟数据库服务
            mock_session = AsyncMock()
            mock_db_service.return_value.get_session.return_value.__aenter__.return_value = mock_session
            
            # 模拟上传记录
            mock_upload_record = MagicMock()
            mock_upload_record.id = "test-upload-id"
            mock_upload_record.filename = "test.txt"
            mock_upload_record.file_type = "txt"
            mock_upload_record.file_size = len(sample_text_content)
            mock_upload_record.file_path = "/tmp/test.txt"
            mock_upload_record.source = "test"
            mock_upload_record.version = "1.0"
            mock_upload_record.uploader = "admin"
            mock_upload_record.status = "pending"
            mock_upload_record.progress = 0
            mock_upload_record.document_count = 0
            mock_upload_record.milvus_ids = []
            mock_upload_record.error_message = None
            mock_upload_record.created_at = "2023-01-01T00:00:00"
            mock_upload_record.processed_at = None
            
            mock_repo.return_value.create_upload_record.return_value = mock_upload_record
            
            # 测试多文件上传
            response = self.client.post(
                "/api/admin/knowledge/upload",
                files=[
                    ("files", ("test1.txt", BytesIO(sample_text_content), "text/plain")),
                    ("files", ("test2.txt", BytesIO(sample_text_content), "text/plain"))
                ],
                data={"source": "test", "version": "1.0"},
                headers={"Authorization": f"Bearer {mock_admin_token}"}
            )
            
            assert response.status_code == 200
            upload_data = response.json()
            assert len(upload_data) == 2
            assert all(item["status"] == "pending" for item in upload_data)



