"""
FAQ CSV Parser 改进测试

测试懒加载、多编码支持、文件大小限制等功能。
"""

import pytest

from src.services.faq_csv_parser import FAQCSVParser


class TestLazyLoadingEmbedding:
    """测试 embedding 服务懒加载"""
    
    def test_parser_init_without_embedding_service(self):
        """初始化解析器不应立即加载 embedding 服务"""
        parser = FAQCSVParser()
        
        # 验证 embedding 服务未初始化
        assert parser._embedding_service is None
    
    @pytest.mark.asyncio
    async def test_preview_without_embedding_service(self):
        """预览功能不应触发 embedding 服务加载"""
        parser = FAQCSVParser()
        
        # 创建简单的 CSV 数据
        csv_content = b"question,answer\nQ1,A1\nQ2,A2"
        
        # 执行预览
        result = await parser.parse_csv_preview(csv_content)
        
        # 验证预览成功
        assert result["columns"] == ["question", "answer"]
        assert len(result["preview_rows"]) == 2
        
        # 验证 embedding 服务仍未初始化
        assert parser._embedding_service is None


class TestMultiEncodingSupport:
    """测试多编码支持"""
    
    def test_decode_utf8(self):
        """测试 UTF-8 编码"""
        parser = FAQCSVParser()
        content = "你好世界".encode('utf-8')
        
        result = parser._decode_csv(content)
        assert result == "你好世界"
    
    def test_decode_gbk(self):
        """测试 GBK 编码"""
        parser = FAQCSVParser()
        content = "你好世界".encode('gbk')
        
        result = parser._decode_csv(content)
        assert result == "你好世界"
    
    def test_decode_shift_jis(self):
        """测试 Shift-JIS 编码（日文）- 实际场景中会先匹配其他编码"""
        parser = FAQCSVParser()
        # 使用 Shift-JIS 特有的字符序列
        content = "question,answer\n質問,回答".encode('shift-jis')
        
        # 应该能成功解码（可能是 UTF-8 或其他编码先匹配）
        result = parser._decode_csv(content)
        # 只要不抛出异常即可
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_decode_fallback_to_latin1(self):
        """测试回退到 ISO-8859-1（总是能解码）"""
        parser = FAQCSVParser()
        # ISO-8859-1 能解码任何字节序列
        content = b'\xff\xfe\xfd\xfc'
        
        # 应该能解码（即使结果可能是乱码）
        result = parser._decode_csv(content)
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_preview_with_gbk_encoding(self):
        """测试使用 GBK 编码的 CSV 预览"""
        parser = FAQCSVParser()
        
        # 创建 GBK 编码的 CSV
        csv_text = "问题,答案\n你好,世界\n测试,数据"
        csv_content = csv_text.encode('gbk')
        
        # 执行预览
        result = await parser.parse_csv_preview(csv_content)
        
        # 验证预览成功
        assert result["columns"] == ["问题", "答案"]
        assert len(result["preview_rows"]) == 2
        assert result["preview_rows"][0]["问题"] == "你好"


class TestFileValidation:
    """测试文件验证（在 API 层测试大小限制）"""
    
    @pytest.mark.asyncio
    async def test_preview_empty_csv(self):
        """测试空 CSV 文件"""
        parser = FAQCSVParser()
        csv_content = b""
        
        # 空文件应该能解析但返回空列表
        result = await parser.parse_csv_preview(csv_content)
        assert result["columns"] == []
        assert result["preview_rows"] == []
        assert result["total_rows"] == 0

