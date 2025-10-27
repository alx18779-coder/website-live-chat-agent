"""
文件解析服务

支持 PDF、Markdown、纯文本等格式的文件解析和智能分块。
"""

import logging
import re
from io import BytesIO
from typing import Dict, List

import markdown
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class FileParser:
    """文件解析服务"""

    SUPPORTED_TYPES = {
        'application/pdf': 'pdf',
        'text/markdown': 'markdown',
        'text/plain': 'txt',
        'text/x-markdown': 'markdown'
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_CHUNK_SIZE = 500  # 最大分块字符数
    MIN_CHUNK_SIZE = 50   # 最小分块字符数

    def __init__(self):
        """初始化文件解析器"""
        self.md = markdown.Markdown(extensions=['codehilite', 'fenced_code'])

    async def parse_file(self, file_content: bytes, filename: str) -> Dict:
        """
        解析文件内容

        Args:
            file_content: 文件内容字节
            filename: 文件名

        Returns:
            Dict: 包含 chunks, metadata 的字典
        """
        try:
            # 检测文件类型
            file_type = self._detect_file_type(file_content, filename)

            # 验证文件大小
            if len(file_content) > self.MAX_FILE_SIZE:
                raise ValueError(f"文件大小超过限制 ({self.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)")

            # 根据文件类型解析内容
            if file_type == 'pdf':
                text_content = await self._parse_pdf(file_content)
            elif file_type == 'markdown':
                text_content = await self._parse_markdown(file_content)
            elif file_type == 'txt':
                text_content = await self._parse_text(file_content)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")

            # 智能分块
            chunks = self._smart_chunk(text_content)

            # 构建元数据
            metadata = {
                'filename': filename,
                'file_type': file_type,
                'file_size': len(file_content),
                'total_chunks': len(chunks),
                'total_chars': len(text_content)
            }

            return {
                'chunks': chunks,
                'metadata': metadata,
                'raw_content': text_content
            }

        except Exception as e:
            logger.error(f"解析文件失败 {filename}: {e}")
            raise

    def _detect_file_type(self, file_content: bytes, filename: str) -> str:
        """
        检测文件类型

        优先使用 python-magic 检测 MIME 类型（如果可用），
        否则回退到基于文件扩展名的检测。

        Args:
            file_content: 文件内容
            filename: 文件名

        Returns:
            str: 文件类型 ('pdf', 'markdown', 'txt')

        Raises:
            ValueError: 不支持的文件类型
        """
        # 尝试使用 python-magic 检测 MIME 类型（惰性导入）
        try:
            import magic  # 惰性导入，避免顶层导入导致模块加载失败
            mime_type = magic.from_buffer(file_content, mime=True)

            # 检查是否支持
            if mime_type in self.SUPPORTED_TYPES:
                return self.SUPPORTED_TYPES[mime_type]
        except (ImportError, Exception) as e:
            # python-magic 不可用或检测失败，回退到扩展名检测
            logger.debug(f"python-magic 检测失败，回退到扩展名检测: {e}")

        # 基于文件扩展名检测
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        ext_mapping = {
            'pdf': 'pdf',
            'md': 'markdown',
            'markdown': 'markdown',
            'txt': 'txt',
            'text': 'txt'
        }

        if ext in ext_mapping:
            return ext_mapping[ext]

        # 不支持的文件类型
        raise ValueError(f"不支持的文件类型: {filename} (扩展名: {ext})")

    async def _parse_pdf(self, file_content: bytes) -> str:
        """解析 PDF 文件"""
        try:
            pdf_reader = PdfReader(BytesIO(file_content))
            text_content = ""

            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"

            if not text_content.strip():
                raise ValueError("PDF 文件中没有可提取的文本内容")

            return text_content.strip()

        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            raise ValueError(f"PDF 文件解析失败: {str(e)}")

    async def _parse_markdown(self, file_content: bytes) -> str:
        """解析 Markdown 文件"""
        try:
            # 解码为文本
            text_content = file_content.decode('utf-8')

            # 转换为 HTML 然后提取纯文本
            html_content = self.md.convert(text_content)

            # 简单的 HTML 标签清理
            clean_text = re.sub(r'<[^>]+>', '', html_content)
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)

            return clean_text.strip()

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                text_content = file_content.decode('gbk')
                html_content = self.md.convert(text_content)
                clean_text = re.sub(r'<[^>]+>', '', html_content)
                return clean_text.strip()
            except Exception as e:
                logger.error(f"Markdown 解析失败: {e}")
                raise ValueError(f"Markdown 文件解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"Markdown 解析失败: {e}")
            raise ValueError(f"Markdown 文件解析失败: {str(e)}")

    async def _parse_text(self, file_content: bytes) -> str:
        """解析纯文本文件"""
        try:
            # 尝试 UTF-8 编码
            text_content = file_content.decode('utf-8')
            return text_content.strip()

        except UnicodeDecodeError:
            try:
                # 尝试 GBK 编码
                text_content = file_content.decode('gbk')
                return text_content.strip()
            except UnicodeDecodeError:
                try:
                    # 尝试 Latin-1 编码
                    text_content = file_content.decode('latin-1')
                    return text_content.strip()
                except Exception as e:
                    logger.error(f"文本文件解析失败: {e}")
                    raise ValueError(f"无法解码文本文件: {str(e)}")
        except Exception as e:
            logger.error(f"文本文件解析失败: {e}")
            raise ValueError(f"文本文件解析失败: {str(e)}")

    def _smart_chunk(self, text: str) -> List[str]:
        """
        智能分块算法

        Args:
            text: 原始文本

        Returns:
            List[str]: 分块后的文本列表
        """
        if not text.strip():
            return []

        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 如果段落太长，进一步分割
            if len(paragraph) > self.MAX_CHUNK_SIZE:
                # 按句子分割
                sentences = re.split(r'[.!?。！？]\s*', paragraph)
                current_chunk = ""

                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    # 如果加上这个句子会超过限制，先保存当前块
                    if len(current_chunk) + len(sentence) + 1 > self.MAX_CHUNK_SIZE:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            # 单个句子太长，直接保存
                            chunks.append(sentence)
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence

                # 保存最后一个块
                if current_chunk:
                    chunks.append(current_chunk.strip())
            else:
                # 段落长度合适，直接保存
                if len(paragraph) >= self.MIN_CHUNK_SIZE:
                    chunks.append(paragraph)

        # 过滤掉太短的块
        filtered_chunks = [chunk for chunk in chunks if len(chunk) >= self.MIN_CHUNK_SIZE]

        logger.info(f"文本分块完成: {len(filtered_chunks)} 个块")
        return filtered_chunks

    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.pdf', '.md', '.markdown', '.txt']

    def get_max_file_size(self) -> int:
        """获取最大文件大小（字节）"""
        return self.MAX_FILE_SIZE



