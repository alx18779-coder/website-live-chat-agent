"""
对话历史数据实体
"""

from pydantic import BaseModel, Field


class ConversationHistory(BaseModel):
    """
    对话历史实体
    
    用于history search返回结果的类型安全封装
    """
    
    role: str = Field(..., description="角色: user/assistant")
    text: str = Field(..., description="消息文本")
    timestamp: int = Field(..., description="消息时间戳")
    
    class Config:
        frozen = False
        extra = "allow"

