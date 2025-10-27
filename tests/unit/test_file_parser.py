"""
文件解析服务单元测试
"""

import pytest
import io
from unittest.mock import patch, MagicMock
from src.services.file_parser import FileParser


class TestFileParser:
    """文件解析器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.parser = FileParser()
    
    @pytest.mark.asyncio
    async def test_parse_pdf_success(self):
        """测试 PDF 解析成功"""
        # 模拟 PDF 内容
        pdf_content = b"PDF content here"
        
        with patch('src.services.file_parser.PdfReader') as mock_pdf_reader:
            # 模拟 PDF 页面
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            
            mock_reader_instance = MagicMock()
            mock_reader_instance.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader_instance
            
            # 执行解析
            result = await self.parser._parse_pdf(pdf_content)
            
            # 验证结果
            assert result == "Sample PDF text content"
            mock_pdf_reader.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_pdf_empty_content(self):
        """测试 PDF 解析空内容"""
        pdf_content = b"PDF content here"
        
        with patch('src.services.file_parser.PdfReader') as mock_pdf_reader:
            # 模拟空页面
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""
            
            mock_reader_instance = MagicMock()
            mock_reader_instance.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader_instance
            
            # 执行解析，应该抛出异常
            with pytest.raises(ValueError, match="PDF 文件中没有可提取的文本内容"):
                await self.parser._parse_pdf(pdf_content)
    
    @pytest.mark.asyncio
    async def test_parse_markdown_success(self):
        """测试 Markdown 解析成功"""
        markdown_content = b"# Title\n\nThis is **bold** text."
        
        result = await self.parser._parse_markdown(markdown_content)
        
        # 验证结果包含清理后的文本
        assert "Title" in result
        assert "bold" in result
    
    @pytest.mark.asyncio
    async def test_parse_text_success(self):
        """测试纯文本解析成功"""
        text_content = b"Simple text content"
        
        result = await self.parser._parse_text(text_content)
        
        assert result == "Simple text content"
    
    @pytest.mark.asyncio
    async def test_parse_text_gbk_encoding(self):
        """测试纯文本 GBK 编码解析"""
        gbk_content = "中文内容".encode('gbk')
        
        result = await self.parser._parse_text(gbk_content)
        
        assert result == "中文内容"
    
    def test_smart_chunk_simple_text(self):
        """测试简单文本分块"""
        # 使用长度超过 MIN_CHUNK_SIZE (50) 的文本
        text = "This is a simple text for chunking that is long enough to pass the minimum chunk size requirement."
        
        chunks = self.parser._smart_chunk(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_smart_chunk_long_text(self):
        """测试长文本分块"""
        # 创建超过最大分块大小的文本
        long_text = "This is a very long text. " * 50  # 约 1250 字符
        
        chunks = self.parser._smart_chunk(long_text)
        
        # 应该被分割成多个块
        assert len(chunks) > 1
        # 每个块都应该在合理范围内
        for chunk in chunks:
            assert len(chunk) <= self.parser.MAX_CHUNK_SIZE
            assert len(chunk) >= self.parser.MIN_CHUNK_SIZE
    
    def test_smart_chunk_paragraphs(self):
        """测试段落分块"""
        # 每个段落都要超过 MIN_CHUNK_SIZE (50)
        text = """First paragraph with some content that is long enough to be kept as a chunk.

Second paragraph with different content that is also long enough.

Third paragraph also with content that meets the minimum size requirement."""
        
        chunks = self.parser._smart_chunk(text)
        
        # 应该按段落分割
        assert len(chunks) == 3
        assert "First paragraph" in chunks[0]
        assert "Second paragraph" in chunks[1]
        assert "Third paragraph" in chunks[2]
    
    def test_smart_chunk_empty_text(self):
        """测试空文本分块"""
        chunks = self.parser._smart_chunk("")
        assert chunks == []
        
        chunks = self.parser._smart_chunk("   ")
        assert chunks == []
    
    def test_detect_file_type_pdf(self):
        """测试 PDF 文件类型检测（基于扩展名，magic 不可用）"""
        pdf_content = b"PDF content"
        
        # Mock magic 不可用（ImportError）
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                   __import__(name, *args, **kwargs) if name != 'magic' else (_ for _ in ()).throw(ImportError())):
            result = self.parser._detect_file_type(pdf_content, "test.pdf")
            assert result == "pdf"
    
    def test_detect_file_type_markdown(self):
        """测试 Markdown 文件类型检测（基于扩展名，magic 不可用）"""
        md_content = b"# Markdown content"
        
        # Mock magic 不可用（ImportError）
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                   __import__(name, *args, **kwargs) if name != 'magic' else (_ for _ in ()).throw(ImportError())):
            result = self.parser._detect_file_type(md_content, "test.md")
            assert result == "markdown"
    
    def test_detect_file_type_by_extension(self):
        """测试通过文件扩展名检测类型（magic 不可用时的回退逻辑）"""
        content = b"Some content"
        
        # Mock magic 不可用
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                   __import__(name, *args, **kwargs) if name != 'magic' else (_ for _ in ()).throw(ImportError())):
            # 测试 PDF 扩展名
            result = self.parser._detect_file_type(content, "test.pdf")
            assert result == "pdf"
            
            # 测试 Markdown 扩展名
            result = self.parser._detect_file_type(content, "test.md")
            assert result == "markdown"
            
            # 测试文本扩展名
            result = self.parser._detect_file_type(content, "test.txt")
            assert result == "txt"
    
    def test_detect_file_type_unsupported(self):
        """测试不支持的文件类型"""
        content = b"Some content"
        
        # Mock magic 不可用
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                   __import__(name, *args, **kwargs) if name != 'magic' else (_ for _ in ()).throw(ImportError())):
            with pytest.raises(ValueError, match="不支持的文件类型"):
                self.parser._detect_file_type(content, "test.xyz")
    
    @pytest.mark.asyncio
    async def test_parse_file_success(self):
        """测试完整文件解析流程"""
        pdf_content = b"PDF content"
        filename = "test.pdf"
        
        with patch.object(self.parser, '_detect_file_type', return_value='pdf'), \
             patch.object(self.parser, '_parse_pdf', return_value='Parsed PDF content'), \
             patch.object(self.parser, '_smart_chunk', return_value=['chunk1', 'chunk2']):
            
            result = await self.parser.parse_file(pdf_content, filename)
            
            assert 'chunks' in result
            assert 'metadata' in result
            assert 'raw_content' in result
            assert result['chunks'] == ['chunk1', 'chunk2']
            assert result['metadata']['filename'] == filename
            assert result['metadata']['file_type'] == 'pdf'
    
    @pytest.mark.asyncio
    async def test_parse_file_size_limit(self):
        """测试文件大小限制"""
        # 创建超过限制的内容
        large_content = b"x" * (self.parser.MAX_FILE_SIZE + 1)
        
        with pytest.raises(ValueError, match="文件大小超过限制"):
            await self.parser.parse_file(large_content, "large.pdf")
    
    @pytest.mark.asyncio
    async def test_parse_file_unsupported_type(self):
        """测试不支持的文件类型"""
        content = b"Some content"
        
        with patch.object(self.parser, '_detect_file_type', side_effect=ValueError("不支持的文件类型")):
            with pytest.raises(ValueError, match="不支持的文件类型"):
                await self.parser.parse_file(content, "test.xyz")
    
    def test_get_supported_extensions(self):
        """测试获取支持的文件扩展名"""
        extensions = self.parser.get_supported_extensions()
        
        assert '.pdf' in extensions
        assert '.md' in extensions
        assert '.txt' in extensions
    
    def test_get_max_file_size(self):
        """测试获取最大文件大小"""
        max_size = self.parser.get_max_file_size()
        
        assert max_size == self.parser.MAX_FILE_SIZE
        assert max_size == 10 * 1024 * 1024  # 10MB



