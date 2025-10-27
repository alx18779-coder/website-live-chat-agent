"""
数据库模型定义

定义管理平台相关的数据表模型。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ConversationHistory(Base):
    """对话历史表"""

    __tablename__ = "conversation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, index=True)
    user_message = Column(Text)
    ai_response = Column(Text)
    retrieved_docs = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<ConversationHistory(id={self.id}, session_id={self.session_id})>"


class AdminUser(Base):
    """管理员用户表"""

    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(64), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(String(1), default="Y", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username={self.username})>"


class AdminAuditLog(Base):
    """管理员操作审计日志表"""

    __tablename__ = "admin_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<AdminAuditLog(id={self.id}, admin_user={self.admin_user}, action={self.action})>"


class KnowledgeFileUpload(Base):
    """知识库文件上传记录表"""

    __tablename__ = "knowledge_file_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, markdown, txt
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(String(500))  # 临时存储路径
    source = Column(String(255))  # 来源
    version = Column(String(50), default="1.0")
    uploader = Column(String(64), nullable=False)  # 上传者用户名

    # 处理状态
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)

    # 处理结果
    document_count = Column(Integer, default=0)  # 生成的文档数量
    milvus_ids = Column(JSON)  # 存入 Milvus 的文档 ID 列表

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<KnowledgeFileUpload(id={self.id}, filename={self.filename}, status={self.status})>"
