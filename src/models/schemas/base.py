"""
Collection Schema基类

定义所有collection schema必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class BaseCollectionSchema(ABC, BaseModel):
    """
    Collection Schema抽象基类

    所有collection schema必须继承此类并实现抽象方法。
    用于定义collection的结构、索引配置等。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    # Collection名称（子类必须定义）
    COLLECTION_NAME: ClassVar[str]

    @classmethod
    @abstractmethod
    def get_milvus_schema(cls) -> dict[str, Any]:
        """
        获取Milvus schema定义

        Returns:
            Milvus格式的schema字典
        """
        pass

    @classmethod
    @abstractmethod
    def get_index_params(cls) -> dict[str, Any]:
        """
        获取索引配置

        Returns:
            索引参数字典
        """
        pass

    @classmethod
    def get_collection_name(cls) -> str:
        """获取collection名称"""
        return cls.COLLECTION_NAME

