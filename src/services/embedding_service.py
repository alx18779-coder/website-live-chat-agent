"""
嵌入服务

提供统一的嵌入向量生成接口。
"""

import logging
from typing import List

from src.services.llm_factory import create_embeddings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入服务类"""

    def __init__(self):
        self.embeddings = create_embeddings()

    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量列表
        """
        try:
            # 使用 LangChain 的嵌入服务
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取文本的嵌入向量

        Args:
            texts: 输入文本列表

        Returns:
            嵌入向量列表
        """
        try:
            # 使用 LangChain 的嵌入服务
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"批量生成嵌入向量失败: {e}")
            raise


# 全局服务实例
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务实例（单例模式）"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service



