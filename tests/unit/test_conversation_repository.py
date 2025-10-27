"""
ConversationRepository 单元测试

测试对话历史 Repository 的 create_conversation 方法。
"""

from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base
from src.db.repositories.conversation_repository import ConversationRepository


@pytest_asyncio.fixture
async def db_session():
    """创建测试数据库会话（使用内存 SQLite）"""
    # 使用异步 SQLite 内存数据库
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话工厂
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # 创建会话
    async with async_session_factory() as session:
        yield session

    # 清理
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_conversation_success(db_session):
    """测试成功创建对话记录"""
    repo = ConversationRepository(db_session)

    # 创建对话
    conversation = await repo.create_conversation(
        session_id="test-session-001",
        user_message="测试问题",
        ai_response="测试回答",
        retrieved_docs=[{"content": "测试文档", "score": 0.95}],
        confidence_score=0.92
    )

    # 验证返回值
    assert conversation.id is not None
    assert conversation.session_id == "test-session-001"
    assert conversation.user_message == "测试问题"
    assert conversation.ai_response == "测试回答"
    assert conversation.confidence_score == 0.92
    assert conversation.created_at is not None
    assert isinstance(conversation.created_at, datetime)
    assert conversation.retrieved_docs == [{"content": "测试文档", "score": 0.95}]

    # 验证数据已保存到数据库
    saved = await repo.get_conversation_by_session_id("test-session-001")
    assert len(saved) == 1
    assert saved[0].id == conversation.id


@pytest.mark.asyncio
async def test_create_conversation_without_optional_fields(db_session):
    """测试创建对话记录（不包含可选字段）"""
    repo = ConversationRepository(db_session)

    conversation = await repo.create_conversation(
        session_id="test-session-002",
        user_message="简单问题",
        ai_response="简单回答"
        # 不传递 retrieved_docs 和 confidence_score
    )

    assert conversation.id is not None
    assert conversation.session_id == "test-session-002"
    assert conversation.user_message == "简单问题"
    assert conversation.ai_response == "简单回答"
    assert conversation.retrieved_docs is None
    assert conversation.confidence_score is None
    assert conversation.created_at is not None


@pytest.mark.asyncio
async def test_create_multiple_conversations_same_session(db_session):
    """测试同一会话的多轮对话"""
    repo = ConversationRepository(db_session)

    # 创建第一轮对话
    await repo.create_conversation(
        session_id="test-session-003",
        user_message="第一个问题",
        ai_response="第一个回答"
    )

    # 创建第二轮对话
    await repo.create_conversation(
        session_id="test-session-003",
        user_message="第二个问题",
        ai_response="第二个回答"
    )

    # 验证同一会话有两条记录
    conversations = await repo.get_conversation_by_session_id("test-session-003")
    assert len(conversations) == 2
    assert conversations[0].id != conversations[1].id

    # 验证按时间排序（早的在前）
    assert conversations[0].created_at <= conversations[1].created_at


@pytest.mark.asyncio
async def test_create_conversation_with_complex_retrieved_docs(db_session):
    """测试创建对话记录（包含复杂的检索文档）"""
    repo = ConversationRepository(db_session)

    retrieved_docs = [
        {
            "content": "文档内容1",
            "score": 0.95,
            "metadata": {"source": "doc1.md", "page": 1}
        },
        {
            "content": "文档内容2",
            "score": 0.88,
            "metadata": {"source": "doc2.md", "page": 5}
        }
    ]

    conversation = await repo.create_conversation(
        session_id="test-session-004",
        user_message="复杂问题",
        ai_response="复杂回答",
        retrieved_docs=retrieved_docs,
        confidence_score=0.91
    )

    assert conversation.id is not None
    assert conversation.retrieved_docs == retrieved_docs
    assert len(conversation.retrieved_docs) == 2
    assert conversation.retrieved_docs[0]["metadata"]["source"] == "doc1.md"


@pytest.mark.asyncio
async def test_create_conversation_with_long_text(db_session):
    """测试创建对话记录（包含长文本）"""
    repo = ConversationRepository(db_session)

    long_message = "这是一个很长的问题。" * 100
    long_response = "这是一个很长的回答。" * 100

    conversation = await repo.create_conversation(
        session_id="test-session-005",
        user_message=long_message,
        ai_response=long_response
    )

    assert conversation.id is not None
    assert len(conversation.user_message) == len(long_message)
    assert len(conversation.ai_response) == len(long_response)


@pytest.mark.asyncio
async def test_create_conversation_with_special_characters(db_session):
    """测试创建对话记录（包含特殊字符）"""
    repo = ConversationRepository(db_session)

    special_message = "特殊字符测试：😀 emoji, 'quotes', \"double quotes\", <html>, {json}"

    conversation = await repo.create_conversation(
        session_id="test-session-006",
        user_message=special_message,
        ai_response="成功处理特殊字符"
    )

    assert conversation.id is not None
    assert conversation.user_message == special_message

