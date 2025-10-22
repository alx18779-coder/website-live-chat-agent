"""
知识库数据实体
"""

from typing import Any

from pydantic import BaseModel, Field


class Knowledge(BaseModel):
    """
    知识库文档实体
    
    用于search返回结果的类型安全封装
    """
    
    text: str = Field(..., description="文档文本内容")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")
    metadata: dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    
    class Config:
        frozen = False
        extra = "allow"

