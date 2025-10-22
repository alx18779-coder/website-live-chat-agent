"""
Repository抽象基类

定义所有Repository必须实现的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

# 泛型类型变量
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Repository抽象基类
    
    所有Repository（Milvus、SQL等）必须实现此接口，
    确保提供统一的数据访问方法。
    """
    
    @abstractmethod
    async def search(self, **kwargs) -> list[T]:
        """
        搜索数据
        
        Returns:
            搜索结果列表（强类型）
        """
        pass
    
    @abstractmethod
    async def insert(self, data: Any) -> int:
        """
        插入数据
        
        Args:
            data: 要插入的数据
        
        Returns:
            插入的记录数
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        删除数据
        
        Args:
            id: 记录ID
        
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        获取记录总数
        
        Returns:
            记录数量
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        pass

