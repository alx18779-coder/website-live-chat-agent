"""
数据库模型单元测试
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import ConversationHistory, AdminAuditLog, Base


class TestDatabaseModels:
    """数据库模型测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建内存数据库用于测试
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def teardown_method(self):
        """测试后清理"""
        self.session.close()
        Base.metadata.drop_all(self.engine)
    
    def test_conversation_history_creation(self):
        """测试对话历史记录创建"""
        conversation = ConversationHistory(
            session_id="test_session_123",
            user_message="Hello, how are you?",
            ai_response="I'm doing well, thank you!",
            retrieved_docs=[{"id": "doc1", "content": "test content"}],
            confidence_score=0.95
        )
        
        self.session.add(conversation)
        self.session.commit()
        
        # 验证记录已创建
        saved_conversation = self.session.query(ConversationHistory).first()
        assert saved_conversation is not None
        assert saved_conversation.session_id == "test_session_123"
        assert saved_conversation.user_message == "Hello, how are you?"
        assert saved_conversation.ai_response == "I'm doing well, thank you!"
        assert saved_conversation.confidence_score == 0.95
        assert saved_conversation.retrieved_docs == [{"id": "doc1", "content": "test content"}]
        assert saved_conversation.created_at is not None
    
    def test_conversation_history_with_null_fields(self):
        """测试对话历史记录 - 空字段"""
        conversation = ConversationHistory(
            session_id="test_session_456",
            user_message="Test message",
            ai_response=None,  # 允许为空
            retrieved_docs=None,  # 允许为空
            confidence_score=None  # 允许为空
        )
        
        self.session.add(conversation)
        self.session.commit()
        
        saved_conversation = self.session.query(ConversationHistory).first()
        assert saved_conversation.ai_response is None
        assert saved_conversation.retrieved_docs is None
        assert saved_conversation.confidence_score is None
    
    def test_conversation_history_json_field(self):
        """测试对话历史记录 - JSON 字段"""
        complex_docs = [
            {
                "id": "doc1",
                "title": "Document 1",
                "content": "This is document content",
                "metadata": {"source": "manual", "version": "1.0"}
            },
            {
                "id": "doc2", 
                "title": "Document 2",
                "content": "Another document",
                "metadata": {"source": "auto", "version": "2.0"}
            }
        ]
        
        conversation = ConversationHistory(
            session_id="test_session_789",
            user_message="Complex query",
            ai_response="Complex response",
            retrieved_docs=complex_docs,
            confidence_score=0.88
        )
        
        self.session.add(conversation)
        self.session.commit()
        
        saved_conversation = self.session.query(ConversationHistory).first()
        assert len(saved_conversation.retrieved_docs) == 2
        assert saved_conversation.retrieved_docs[0]["id"] == "doc1"
        assert saved_conversation.retrieved_docs[1]["metadata"]["version"] == "2.0"
    
    def test_admin_audit_log_creation(self):
        """测试管理员审计日志创建"""
        import uuid
        audit_log = AdminAuditLog(
            admin_user="admin",
            action="CREATE_DOCUMENT",
            resource_type="knowledge_document",
            resource_id=uuid.uuid4(),  # 使用 UUID 对象而不是字符串
            details={"title": "New Document", "content_length": 1000}
        )
        
        self.session.add(audit_log)
        self.session.commit()
        
        # 验证记录已创建
        saved_log = self.session.query(AdminAuditLog).first()
        assert saved_log is not None
        assert saved_log.admin_user == "admin"
        assert saved_log.action == "CREATE_DOCUMENT"
        assert saved_log.resource_type == "knowledge_document"
        assert saved_log.resource_id == audit_log.resource_id  # 验证 UUID
        assert saved_log.details == {"title": "New Document", "content_length": 1000}
        assert saved_log.created_at is not None
    
    def test_admin_audit_log_with_null_fields(self):
        """测试管理员审计日志 - 空字段"""
        audit_log = AdminAuditLog(
            admin_user="admin",
            action="LOGIN",
            resource_type=None,  # 允许为空
            resource_id=None,   # 允许为空
            details=None        # 允许为空
        )
        
        self.session.add(audit_log)
        self.session.commit()
        
        saved_log = self.session.query(AdminAuditLog).first()
        assert saved_log.resource_type is None
        assert saved_log.resource_id is None
        assert saved_log.details is None
    
    def test_admin_audit_log_json_details(self):
        """测试管理员审计日志 - JSON 详情字段"""
        complex_details = {
            "operation": "BULK_UPDATE",
            "affected_documents": ["doc1", "doc2", "doc3"],
            "changes": {
                "metadata": {"updated": True},
                "content": {"length_before": 100, "length_after": 150}
            },
            "performance": {
                "duration_ms": 2500,
                "memory_usage_mb": 45.2
            }
        }
        
        audit_log = AdminAuditLog(
            admin_user="admin",
            action="BULK_UPDATE_DOCUMENTS",
            resource_type="knowledge_document",
            details=complex_details
        )
        
        self.session.add(audit_log)
        self.session.commit()
        
        saved_log = self.session.query(AdminAuditLog).first()
        assert saved_log.details["operation"] == "BULK_UPDATE"
        assert len(saved_log.details["affected_documents"]) == 3
        assert saved_log.details["performance"]["duration_ms"] == 2500
    
    def test_model_timestamps(self):
        """测试模型时间戳"""
        conversation = ConversationHistory(
            session_id="test_session",
            user_message="Test",
            ai_response="Test response"
        )
        
        # 记录创建前的时间
        before_creation = datetime.utcnow()
        
        self.session.add(conversation)
        self.session.commit()
        
        # 记录创建后的时间
        after_creation = datetime.utcnow()
        
        saved_conversation = self.session.query(ConversationHistory).first()
        created_at = saved_conversation.created_at
        
        # 验证时间戳在合理范围内
        assert before_creation <= created_at <= after_creation
    
    def test_model_primary_keys(self):
        """测试模型主键"""
        conversation = ConversationHistory(
            session_id="test_session",
            user_message="Test",
            ai_response="Test response"
        )
        
        self.session.add(conversation)
        self.session.commit()
        
        saved_conversation = self.session.query(ConversationHistory).first()
        
        # 验证主键存在且为 UUID
        assert saved_conversation.id is not None
        assert str(saved_conversation.id).count('-') == 4  # UUID 格式
    
    def test_model_relationships(self):
        """测试模型关系（如果有外键关系）"""
        # 这里可以测试模型之间的关系
        # 目前模型之间没有直接关系，但可以测试基本功能
        
        conversation = ConversationHistory(
            session_id="test_session",
            user_message="Test",
            ai_response="Test response"
        )
        
        audit_log = AdminAuditLog(
            admin_user="admin",
            action="VIEW_CONVERSATION",
            resource_id=conversation.id
        )
        
        self.session.add(conversation)
        self.session.add(audit_log)
        self.session.commit()
        
        # 验证两个记录都正确保存
        assert self.session.query(ConversationHistory).count() == 1
        assert self.session.query(AdminAuditLog).count() == 1
    
    def test_model_constraints(self):
        """测试模型约束"""
        # 测试必填字段
        conversation = ConversationHistory(
            # 缺少必填字段 session_id
            user_message="Test",
            ai_response="Test response"
        )
        
        # 应该抛出异常
        with pytest.raises(Exception):
            self.session.add(conversation)
            self.session.commit()
    
    def test_model_indexes(self):
        """测试模型索引（通过查询性能间接测试）"""
        # 创建多条记录
        for i in range(10):
            conversation = ConversationHistory(
                session_id=f"session_{i}",
                user_message=f"Message {i}",
                ai_response=f"Response {i}"
            )
            self.session.add(conversation)
        
        self.session.commit()
        
        # 测试按 session_id 查询（应该有索引）
        conversations = self.session.query(ConversationHistory).filter(
            ConversationHistory.session_id == "session_5"
        ).all()
        
        assert len(conversations) == 1
        assert conversations[0].user_message == "Message 5"
