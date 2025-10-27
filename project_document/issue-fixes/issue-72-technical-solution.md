# Issue #72 技术方案文档

**文档类型**: 架构师技术方案  
**Issue 编号**: #72  
**负责架构师**: AR (Architect AI)  
**创建日期**: 2025-10-27  
**目标实施者**: LD (Lead Developer)

---

## 问题定性

### 架构问题分析

**问题类型**: P0 级架构实现缺失  
**严重程度**: 🔴 高 - 导致管理平台核心功能（对话监控）完全无法使用

**根本原因**:
- ✅ 数据模型已定义 (`ConversationHistory`)
- ✅ Repository 查询方法已实现
- ✅ 管理平台 API 已实现
- ❌ **数据写入逻辑缺失** - 对话数据未保存到 PostgreSQL

**违反的架构约束**:
- ADR-0010（运营管理平台）第 238-246 行：数据同步流程要求
- ADR-0010 P0 约束：数据持久化是核心功能
- ADR-0009（Repository 模式）：统一数据访问层原则

---

## 技术方案

### 方案总览

**核心思路**: 在 API 响应流程中，从 LangGraph Agent 执行结果提取数据，通过 Repository 异步保存到 PostgreSQL。

**架构原则**:
```
遵循约束:
✅ 使用 Repository 模式（符合 ADR-0009）
✅ 异步保存，不阻塞用户响应（符合 ADR-0010 性能要求）
✅ 保存失败不影响聊天功能（错误隔离）
✅ 完整的错误处理和日志记录
```

---

### 实施步骤

## Step 1: 扩展 ConversationRepository（核心）

### 📁 文件位置
`src/db/repositories/conversation_repository.py`

### 📝 实施内容

在 `ConversationRepository` 类中添加 `create_conversation()` 方法：

```python
# 位置：第 183 行之后（log_admin_action 方法之后）

async def create_conversation(
    self,
    session_id: str,
    user_message: str,
    ai_response: str,
    retrieved_docs: Optional[List[Dict[str, Any]]] = None,
    confidence_score: Optional[float] = None
) -> ConversationHistory:
    """
    创建对话历史记录
    
    Args:
        session_id: 会话ID（用于关联同一会话的多轮对话）
        user_message: 用户消息内容
        ai_response: AI 回复内容
        retrieved_docs: 检索到的知识库文档列表，格式：
                       [{"content": "...", "score": 0.95, "metadata": {...}}, ...]
        confidence_score: 对话置信度分数（0.0-1.0）
        
    Returns:
        ConversationHistory: 创建的对话记录对象（包含生成的 ID 和时间戳）
        
    Raises:
        SQLAlchemyError: 数据库操作失败时抛出
        
    Example:
        >>> repo = ConversationRepository(session)
        >>> conversation = await repo.create_conversation(
        ...     session_id="session-123",
        ...     user_message="产品价格是多少？",
        ...     ai_response="我们的产品价格为 299 元。",
        ...     retrieved_docs=[{"content": "价格说明...", "score": 0.95}],
        ...     confidence_score=0.92
        ... )
        >>> print(conversation.id)  # UUID对象
    """
    # 创建对话记录对象
    conversation = ConversationHistory(
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
        retrieved_docs=retrieved_docs,
        confidence_score=confidence_score
    )
    
    # 添加到会话
    self.session.add(conversation)
    
    # 提交到数据库
    await self.session.commit()
    
    # 刷新对象以获取数据库生成的字段（id, created_at）
    await self.session.refresh(conversation)
    
    return conversation
```

### 🎯 设计要点

1. **类型安全**: 
   - 使用类型提示确保参数类型正确
   - `retrieved_docs` 和 `confidence_score` 为可选参数（某些场景可能没有）

2. **返回值**: 
   - 返回完整的 `ConversationHistory` 对象
   - 包含数据库生成的 `id` 和 `created_at`（通过 `refresh()` 获取）

3. **事务处理**:
   - 使用 `commit()` 确保数据持久化
   - 异常会自动回滚（由 SQLAlchemy 处理）

4. **文档字符串**:
   - 遵循 Google 风格
   - 包含完整的参数说明和示例

---

## Step 2: API 层集成 - 非流式响应

### 📁 文件位置
`src/api/v1/openai_compat.py`

### 📝 实施内容

在 `_non_stream_response()` 函数中集成保存逻辑：

#### 位置：第 316 行之后（提取 AI 响应之后）

```python
# === 现有代码（第 310-316 行）===
# 提取 AI 响应
ai_message = result["messages"][-1]
if isinstance(ai_message, AIMessage):
    response_content = ai_message.content
else:
    response_content = str(ai_message)

# === 新增代码：保存对话到 PostgreSQL ===

# 异步保存对话历史（不阻塞响应）
try:
    from src.db.base import DatabaseService
    from src.db.repositories.conversation_repository import ConversationRepository
    
    # 获取数据库服务实例
    db_service = DatabaseService(settings.postgres_url)
    
    # 使用上下文管理器确保连接正确关闭
    async with db_service.get_session() as db_session:
        repo = ConversationRepository(db_session)
        
        # 保存对话记录
        conversation = await repo.create_conversation(
            session_id=session_id,
            user_message=user_message,
            ai_response=response_content,
            retrieved_docs=result.get("retrieved_docs"),
            confidence_score=result.get("confidence_score")
        )
        
        logger.info(
            f"✅ Conversation saved successfully | "
            f"session_id={session_id} | "
            f"conversation_id={conversation.id}"
        )
        
except Exception as e:
    # 保存失败不影响用户响应（符合架构要求）
    # 只记录错误日志，不抛出异常
    logger.error(
        f"❌ Failed to save conversation to PostgreSQL | "
        f"session_id={session_id} | "
        f"error={str(e)} | "
        f"error_type={type(e).__name__}"
    )
    # 注意：不要 raise，让响应正常返回

# === 继续现有代码（第 317-339 行）===
# 计算 Token 使用（简化版，使用字符数估算）
prompt_tokens = len(user_message) // 4
...
```

### 🎯 实施要点

1. **导入位置**:
   - 建议在 try 块内导入，避免循环导入问题
   - 如果确认无循环依赖，可以移到文件顶部

2. **错误隔离**:
   - 使用 try-except 包裹保存逻辑
   - 保存失败**不要抛出异常**，只记录日志
   - 确保用户始终能收到响应

3. **数据库连接管理**:
   - 使用 `DatabaseService.get_session()` 上下文管理器
   - 自动处理连接的创建和关闭
   - 避免连接泄漏

4. **日志记录**:
   - 成功：记录 `session_id` 和 `conversation_id`
   - 失败：记录 `session_id`、错误信息和错误类型
   - 使用结构化日志格式（便于监控和排查）

---

## Step 3: API 层集成 - 流式响应

### 📁 文件位置
`src/api/v1/openai_compat.py`

### 📝 实施内容

在 `_stream_response()` 函数中集成保存逻辑：

#### 挑战：流式响应需要收集完整响应

流式响应的 AI 回复是分块发送的，需要先收集完整响应再保存。

#### 位置：`_stream_response()` 函数内部修改

```python
async def _stream_response(
    user_message: str,
    session_id: str,
    completion_id: str,
    created_timestamp: int,
    model: str,
    requested_model: str,
) -> AsyncGenerator[str, None]:
    """流式响应（SSE）"""
    from src.agent.main.nodes import _is_valid_user_query
    
    app = get_agent_app()
    
    # ... 现有的消息验证逻辑 ...
    
    # === 新增：用于收集完整响应和检索文档 ===
    collected_response = ""
    collected_retrieved_docs = None
    collected_confidence_score = None
    
    try:
        async for chunk in app.astream(initial_state, config):
            logger.debug(f"📦 Agent chunk: {list(chunk.keys())}")
            
            # === 新增：收集检索文档和置信度 ===
            if "retrieve" in chunk:
                node_output = chunk["retrieve"]
                if "retrieved_docs" in node_output:
                    collected_retrieved_docs = node_output["retrieved_docs"]
            
            if "llm" in chunk:
                node_output = chunk["llm"]
                if "confidence_score" in node_output:
                    collected_confidence_score = node_output.get("confidence_score")
                
                # 提取 AI 消息
                messages = node_output.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if isinstance(last_message, AIMessage):
                        content = last_message.content
                        
                        # === 新增：累积完整响应 ===
                        collected_response += content
                        
                        # 现有的流式输出逻辑
                        if content:
                            chunk_obj = ChatCompletionChunk(...)
                            yield f"data: {chunk_obj.model_dump_json()}\n\n"
        
        # 流式响应结束
        final_chunk = ChatCompletionChunk(...)
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
        # === 新增：流式响应完成后保存对话 ===
        if collected_response:
            try:
                from src.db.base import DatabaseService
                from src.db.repositories.conversation_repository import ConversationRepository
                
                db_service = DatabaseService(settings.postgres_url)
                
                async with db_service.get_session() as db_session:
                    repo = ConversationRepository(db_session)
                    
                    conversation = await repo.create_conversation(
                        session_id=session_id,
                        user_message=user_message,
                        ai_response=collected_response,
                        retrieved_docs=collected_retrieved_docs,
                        confidence_score=collected_confidence_score
                    )
                    
                    logger.info(
                        f"✅ Streaming conversation saved | "
                        f"session_id={session_id} | "
                        f"conversation_id={conversation.id}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"❌ Failed to save streaming conversation | "
                    f"session_id={session_id} | "
                    f"error={str(e)}"
                )
        
    except Exception as e:
        logger.error(f"❌ Agent streaming failed: {e}")
        # 错误处理...
```

### 🎯 实施要点

1. **响应收集**:
   - 使用 `collected_response` 累积所有内容块
   - 在流式响应过程中持续追加

2. **检索文档收集**:
   - 从 `retrieve` 节点提取 `retrieved_docs`
   - 从 `llm` 节点提取 `confidence_score`

3. **保存时机**:
   - 在流式响应**完全结束后**保存
   - 确保 `collected_response` 非空（避免保存空对话）

4. **错误处理**:
   - 保存失败不影响流式响应
   - 只记录错误日志

---

## Step 4: 单元测试

### 📁 文件位置
`tests/unit/repositories/test_conversation_repository.py`（新建）

### 📝 测试用例

```python
"""
测试 ConversationRepository
"""

import pytest
from datetime import datetime
from src.db.repositories.conversation_repository import ConversationRepository
from src.db.models import ConversationHistory


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
    assert conversation.retrieved_docs is None
    assert conversation.confidence_score is None


@pytest.mark.asyncio
async def test_create_multiple_conversations_same_session(db_session):
    """测试同一会话的多轮对话"""
    repo = ConversationRepository(db_session)
    
    # 创建第一轮对话
    conv1 = await repo.create_conversation(
        session_id="test-session-003",
        user_message="第一个问题",
        ai_response="第一个回答"
    )
    
    # 创建第二轮对话
    conv2 = await repo.create_conversation(
        session_id="test-session-003",
        user_message="第二个问题",
        ai_response="第二个回答"
    )
    
    # 验证同一会话有两条记录
    conversations = await repo.get_conversation_by_session_id("test-session-003")
    assert len(conversations) == 2
    assert conversations[0].id != conversations[1].id
```

### 📁 文件位置
`tests/integration/test_openai_compat_with_db.py`（新建或扩展）

### 📝 集成测试

```python
"""
测试 OpenAI 兼容 API 与数据库集成
"""

import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_chat_completions_saves_to_db(db_session):
    """测试聊天 API 调用后对话被保存到数据库"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "集成测试消息"}]
            },
            headers={"Authorization": "Bearer test-api-key"}
        )
        
        assert response.status_code == 200
        
        # 验证数据库中有记录
        from src.db.repositories.conversation_repository import ConversationRepository
        repo = ConversationRepository(db_session)
        
        # 注意：需要从响应中提取 session_id 或使用测试时指定的 session_id
        conversations = await repo.get_conversations(skip=0, limit=10)
        assert len(conversations) > 0
        
        # 验证最新的对话记录
        latest = conversations[0]
        assert latest.user_message == "集成测试消息"
        assert latest.ai_response is not None
```

---

## 架构约束与验证标准

### P0 约束（必须遵守）

✅ **向后兼容性**
- 不修改现有 API 接口签名
- 保持现有功能正常工作

✅ **性能要求**
- 保存操作不增加响应延迟 >50ms
- 使用异步操作，不阻塞用户响应

✅ **错误隔离**
- 保存失败不影响聊天功能
- 用户始终能收到 AI 响应

✅ **数据完整性**
- 所有字段正确保存
- `created_at` 时间戳准确

### 验收标准

#### 功能验证
- [ ] 非流式响应：对话记录成功保存到 `conversation_history` 表
- [ ] 流式响应：对话记录成功保存到 `conversation_history` 表
- [ ] 管理平台查询接口返回正确数据
- [ ] 所有字段（session_id, user_message, ai_response, retrieved_docs, confidence_score）正确保存

#### 异常处理验证
- [ ] PostgreSQL 连接失败时，聊天功能正常工作
- [ ] 保存失败时有错误日志记录
- [ ] 并发请求时保存逻辑正常工作

#### 性能验证
- [ ] 保存操作不显著增加响应延迟（<50ms）
- [ ] 并发场景下数据库连接池正常工作

#### 测试覆盖验证
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] 手动测试通过（按 Issue #72 复现步骤）

---

## 风险评估

### 🟢 低风险

**数据库连接池耗尽**
- **可能性**: 低
- **影响**: 保存失败，但不影响聊天
- **缓解**: 使用上下文管理器确保连接正确关闭

**数据类型不匹配**
- **可能性**: 低
- **影响**: 保存失败
- **缓解**: 类型提示 + 单元测试验证

### 🟡 中风险

**PostgreSQL 服务不可用**
- **可能性**: 中
- **影响**: 所有对话无法保存到数据库
- **缓解**: 错误隔离 + 日志记录 + 监控告警

---

## 实施时间估算

| 任务 | 预估时间 | 责任人 |
|-----|---------|--------|
| Step 1: Repository 方法 | 30 分钟 | LD |
| Step 2: 非流式 API 集成 | 1 小时 | LD |
| Step 3: 流式 API 集成 | 1.5 小时 | LD |
| Step 4: 单元测试 | 1 小时 | LD |
| Step 5: 集成测试 | 1 小时 | LD |
| Code Review | 30 分钟 | AR |
| QA 验证 | 2 小时 | QA |
| **总计** | **7.5 小时** | - |

---

## 参考资料

- **ADR-0009**: Repository 模式重构 - 统一数据访问层
- **ADR-0010**: 运营管理平台架构设计
- **Epic-005**: 运营管理平台业务需求
- **数据模型**: `src/db/models.py` - ConversationHistory
- **现有 Repository**: `src/db/repositories/conversation_repository.py`

---

## 注意事项

### ⚠️ 重要提醒

1. **不要修改现有方法签名**
   - 只添加新方法 `create_conversation()`
   - 不要修改现有的查询方法

2. **保持错误隔离**
   - 保存失败**不要抛出异常**到 API 层
   - 只记录日志，让响应正常返回

3. **数据库连接管理**
   - 始终使用上下文管理器 (`async with`)
   - 确保连接在使用后正确关闭

4. **日志记录规范**
   - 成功：使用 `logger.info()`
   - 失败：使用 `logger.error()`
   - 包含关键上下文（session_id, conversation_id 等）

5. **类型安全**
   - 使用完整的类型提示
   - 遵循 Python 3.10+ 最佳实践

---

## 架构师签名

**架构师**: AR (Architect AI)  
**审查日期**: 2025-10-27  
**方案版本**: v1.0  
**状态**: ✅ 已批准，可开始实施

---

**LD 实施前必读**：
1. 完整阅读本文档
2. 理解架构约束和设计要点
3. 有疑问先与 AR 沟通
4. 实施完成后提交 PR，由 AR Code Review

