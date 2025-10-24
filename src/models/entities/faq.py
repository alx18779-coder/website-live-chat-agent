"""
FAQ数据实体
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FAQ(BaseModel):
    """
    FAQ数据实体
    
    用于search返回结果的类型安全封装
    """
    
    model_config = ConfigDict(frozen=False, extra="allow")
    
    text: str = Field(..., description="FAQ文本内容")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")
    metadata: dict[str, Any] = Field(default_factory=dict, description="FAQ元数据")
    
    @property
    def question(self) -> str:
        """获取问题"""
        return self.metadata.get("question", "")
    
    @property
    def answer(self) -> str:
        """获取答案"""
        return self.metadata.get("answer", "")

