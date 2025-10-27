"""
FAQ CSV 解析服务

提供灵活的CSV解析和处理功能，支持用户自定义列配置。
"""

import csv
import io
import logging
import uuid
from typing import Any

from src.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

# 常见CSV编码列表（按优先级排序）
COMMON_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'shift-jis', 'euc-kr', 'iso-8859-1', 'utf-16']


class FAQCSVParser:
    """FAQ CSV 解析器 - 支持灵活的列配置"""

    def __init__(self) -> None:
        """初始化解析器（不立即加载embedding服务）"""
        self._embedding_service = None  # 懒加载

    def _get_embedding_service(self):
        """懒加载embedding服务（仅在process_csv时需要）"""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    def _decode_csv(self, file_content: bytes) -> str:
        """
        尝试多种编码解码CSV

        Args:
            file_content: 原始字节内容

        Returns:
            解码后的文本

        Raises:
            ValueError: 所有编码都失败
        """
        # 尝试常见编码
        for encoding in COMMON_ENCODINGS:
            try:
                text = file_content.decode(encoding)
                logger.info(f"成功使用 {encoding} 编码解析CSV")
                return text
            except (UnicodeDecodeError, LookupError):
                continue

        # 所有编码都失败
        raise ValueError(
            f"无法解码CSV文件，已尝试编码: {', '.join(COMMON_ENCODINGS)}。"
            "请确保文件是有效的CSV格式。"
        )

    async def parse_csv_preview(
        self,
        file_content: bytes
    ) -> dict[str, Any]:
        """
        解析CSV并返回预览信息

        Args:
            file_content: CSV文件内容

        Returns:
            {
                "columns": ["question", "answer"],
                "preview_rows": [...],  # 前5行
                "total_rows": 100,
                "detected_language": "zh"
            }
        """
        text = self._decode_csv(file_content)
        reader = csv.DictReader(io.StringIO(text))

        columns = list(reader.fieldnames or [])
        rows = list(reader)

        # 自动检测语言
        detected_language = self._detect_language(rows, columns)

        return {
            "columns": columns,
            "preview_rows": rows[:5],
            "total_rows": len(rows),
            "detected_language": detected_language,
        }

    async def process_csv(
        self,
        file_content: bytes,
        text_columns: list[str],
        embedding_columns: list[str],
        text_template: str = "{question}\n答：{answer}",
        language: str = "zh",
    ) -> list[dict[str, Any]]:
        """
        根据配置处理CSV

        Args:
            file_content: CSV文件内容
            text_columns: 用于生成text的列名
            embedding_columns: 用于生成embedding的列名
            text_template: 文本拼接模板
            language: 语言标记

        Returns:
            处理后的FAQ列表
        """
        text = self._decode_csv(file_content)
        reader = csv.DictReader(io.StringIO(text))

        faqs = []
        for row in reader:
            # 跳过空行
            if not any(row.values()):
                continue

            try:
                # 生成text（根据模板）
                text_content = self._generate_text(row, text_columns, text_template)

                # 生成embedding（根据配置的列）
                embedding_content = self._generate_embedding_text(row, embedding_columns)
                embedding = await self._get_embedding_service().get_embedding(embedding_content)

                # 构建FAQ
                faqs.append({
                    "id": str(uuid.uuid4()),
                    "text": text_content,
                    "embedding": embedding,
                    "metadata": {
                        **row,  # 保存所有原始列
                        "language": language,
                        "text_template": text_template,
                        "embedding_source": ",".join(embedding_columns),
                    }
                })
            except Exception as e:
                logger.warning(f"处理CSV行失败，跳过: {e}")
                continue

        logger.info(f"成功处理 {len(faqs)} 条FAQ")
        return faqs

    def _generate_text(
        self,
        row: dict[str, str],
        columns: list[str],
        template: str
    ) -> str:
        """根据模板生成text"""
        try:
            return template.format(**row)
        except KeyError:
            # 降级：直接拼接
            return " ".join(row.get(col, "") for col in columns)

    def _generate_embedding_text(
        self,
        row: dict[str, str],
        columns: list[str]
    ) -> str:
        """生成用于embedding的文本"""
        return " ".join(row.get(col, "") for col in columns)

    def _detect_language(
        self,
        rows: list[dict],
        columns: list[str]
    ) -> str:
        """简单的语言检测"""
        if not rows:
            return "zh"

        # 检查第一行是否包含中文
        first_row = rows[0]
        sample_text = " ".join(str(first_row.get(col, "")) for col in columns[:2])

        # 简单判断：是否包含中文字符
        for char in sample_text:
            if '\u4e00' <= char <= '\u9fff':
                return "zh"

        return "en"

