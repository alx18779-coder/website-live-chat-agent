"""
Repository模块

提供统一的数据访问层接口和工厂函数。
"""

from src.repositories.base import BaseRepository
from src.repositories.milvus.history_repository import HistoryRepository
from src.repositories.milvus.knowledge_repository import KnowledgeRepository
from src.repositories.milvus.faq_repository import FAQRepository

# 单例实例（懒加载）
_knowledge_repository: KnowledgeRepository | None = None
_history_repository: HistoryRepository | None = None
_faq_repository: FAQRepository | None = None


def get_knowledge_repository() -> KnowledgeRepository:
    """
    获取知识库Repository单例
    
    Returns:
        KnowledgeRepository实例
    """
    global _knowledge_repository
    if _knowledge_repository is None:
        # 导入Milvus客户端（避免循环导入）
        from src.services.milvus_service import milvus_service
        
        if milvus_service.client is None:
            raise RuntimeError(
                "Milvus client not initialized. "
                "Call milvus_service.initialize() first."
            )
        
        _knowledge_repository = KnowledgeRepository(milvus_service.client)
    
    return _knowledge_repository


def get_history_repository() -> HistoryRepository:
    """
    获取对话历史Repository单例
    
    Returns:
        HistoryRepository实例
    """
    global _history_repository
    if _history_repository is None:
        # 导入Milvus客户端（避免循环导入）
        from src.services.milvus_service import milvus_service
        
        if milvus_service.client is None:
            raise RuntimeError(
                "Milvus client not initialized. "
                "Call milvus_service.initialize() first."
            )
        
        _history_repository = HistoryRepository(milvus_service.client)
    
    return _history_repository


def get_faq_repository() -> FAQRepository:
    """
    获取FAQ Repository单例
    
    Returns:
        FAQRepository实例
    """
    global _faq_repository
    if _faq_repository is None:
        # 导入Milvus客户端（避免循环导入）
        from src.services.milvus_service import milvus_service
        
        if milvus_service.client is None:
            raise RuntimeError(
                "Milvus client not initialized. "
                "Call milvus_service.initialize() first."
            )
        
        _faq_repository = FAQRepository(milvus_service.client)
    
    return _faq_repository


async def initialize_repositories() -> None:
    """
    初始化所有Repository的collection
    
    应该在应用启动时调用一次。
    """
    knowledge_repo = get_knowledge_repository()
    history_repo = get_history_repository()
    faq_repo = get_faq_repository()
    
    await knowledge_repo.initialize()
    await history_repo.initialize()
    await faq_repo.initialize()


def reset_repositories() -> None:
    """
    重置Repository单例（主要用于测试）
    """
    global _knowledge_repository, _history_repository, _faq_repository
    _knowledge_repository = None
    _history_repository = None
    _faq_repository = None


__all__ = [
    "BaseRepository",
    "KnowledgeRepository",
    "HistoryRepository",
    "FAQRepository",
    "get_knowledge_repository",
    "get_history_repository",
    "get_faq_repository",
    "initialize_repositories",
    "reset_repositories",
]

