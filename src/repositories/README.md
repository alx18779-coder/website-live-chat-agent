# Repository模块

## 概述

Repository模式为数据访问提供统一、类型安全的抽象层，支持Milvus向量数据库和未来的关系数据库扩展。

## 快速开始

### 使用知识库Repository

```python
from src.repositories import get_knowledge_repository

# 获取Repository实例（单例）
knowledge_repo = get_knowledge_repository()

# 搜索知识库
results = await knowledge_repo.search(
    query_embedding=embedding,
    top_k=5,
    score_threshold=0.7  # 可选
)

# 插入文档
documents = [
    {
        "id": "doc_001",
        "text": "文档内容",
        "embedding": [0.1, 0.2, ...],
        "metadata": {"source": "manual"}
    }
]
inserted_count = await knowledge_repo.insert(documents)
```

### 使用对话历史Repository

```python
from src.repositories import get_history_repository

# 获取Repository实例
history_repo = get_history_repository()

# 按会话ID查询历史
history = await history_repo.search_by_session(
    session_id="session_123",
    limit=10
)

# 插入对话消息
messages = [
    {
        "id": "msg_001",
        "session_id": "session_123",
        "role": "user",
        "text": "用户问题",
        "embedding": [0.1, 0.2, ...],
        "timestamp": 1729612800
    }
]
inserted_count = await history_repo.insert(messages)
```

## 架构设计

### 三层架构

```
BaseRepository (抽象层)
    ↓
BaseMilvusRepository (Milvus通用层)
    ↓
KnowledgeRepository / HistoryRepository (业务层)
```

### 类型安全

所有Repository都是泛型类型，返回强类型实体：

```python
class KnowledgeRepository(BaseMilvusRepository[Knowledge]):
    async def search(...) -> list[Knowledge]:
        ...

class HistoryRepository(BaseMilvusRepository[ConversationHistory]):
    async def search_by_session(...) -> list[ConversationHistory]:
        ...
```

## 添加新的数据源

### 步骤1: 定义Schema

```python
# src/models/schemas/faq_schema.py
from typing import Any, ClassVar
from pymilvus import DataType
from src.models.schemas.base import BaseCollectionSchema
from src.core.config import settings

class FAQCollectionSchema(BaseCollectionSchema):
    COLLECTION_NAME: ClassVar[str] = "faq_collection"

    @classmethod
    def get_milvus_schema(cls) -> dict[str, Any]:
        return {
            "fields": [
                {"name": "id", "dtype": DataType.VARCHAR, "max_length": 64, "is_primary": True},
                {"name": "question", "dtype": DataType.VARCHAR, "max_length": 1000},
                {"name": "answer", "dtype": DataType.VARCHAR, "max_length": 5000},
                {"name": "embedding", "dtype": DataType.FLOAT_VECTOR, "dim": settings.embedding_dim},
                {"name": "category", "dtype": DataType.VARCHAR, "max_length": 100},
            ],
            "description": "FAQ知识库",
            "enable_dynamic_field": False,
        }

    @classmethod
    def get_index_params(cls) -> dict[str, Any]:
        return {
            "field_name": "embedding",
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
```

### 步骤2: 定义Entity

```python
# src/models/entities/faq.py
from pydantic import BaseModel, ConfigDict, Field

class FAQ(BaseModel):
    model_config = ConfigDict(frozen=False, extra="allow")
    
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")
    category: str = Field(default="", description="分类")
```

### 步骤3: 创建Repository

```python
# src/repositories/milvus/faq_repository.py
from src.models.entities.faq import FAQ
from src.models.schemas.faq_schema import FAQCollectionSchema
from src.repositories.milvus.base_milvus_repository import BaseMilvusRepository

class FAQRepository(BaseMilvusRepository[FAQ]):
    def __init__(self) -> None:
        super().__init__(collection_schema=FAQCollectionSchema)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        category: str | None = None,
    ) -> list[FAQ]:
        """搜索FAQ"""
        expr = f'category == "{category}"' if category else None
        
        results = await self._search_vectors(
            query_embedding=query_embedding,
            output_fields=["question", "answer", "category"],
            limit=top_k,
            expr=expr,
        )
        
        return [
            FAQ(
                question=r["question"],
                answer=r["answer"],
                score=r["score"],
                category=r["category"],
            )
            for r in results
        ]

    async def insert(self, faqs: list[dict]) -> int:
        """插入FAQ"""
        data = [
            {
                "id": faq["id"],
                "question": faq["question"],
                "answer": faq["answer"],
                "embedding": faq["embedding"],
                "category": faq.get("category", "general"),
            }
            for faq in faqs
        ]
        return await self._insert_data(data)
```

### 步骤4: 注册Repository

```python
# src/repositories/__init__.py
from src.repositories.milvus.faq_repository import FAQRepository

_faq_repository: FAQRepository | None = None

async def initialize_repositories() -> None:
    global _faq_repository
    # ... existing code ...
    
    if _faq_repository is None:
        _faq_repository = FAQRepository()
        await _faq_repository.initialize()
        logger.info("✅ FAQRepository initialized.")

@lru_cache(maxsize=1)
def get_faq_repository() -> FAQRepository:
    if _faq_repository is None:
        raise RuntimeError("FAQRepository not initialized.")
    return _faq_repository
```

### 步骤5: 使用新Repository

```python
from src.repositories import get_faq_repository

faq_repo = get_faq_repository()
faqs = await faq_repo.search(
    query_embedding=embedding,
    top_k=5,
    category="产品"
)
```

**总工作量**: ~2小时（创建4个文件，~100行代码）

## 初始化

Repository在应用启动时自动初始化（`src/main.py`的`lifespan`）：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化Milvus
    await milvus_service.initialize()
    
    # 初始化Repository层
    from src.repositories import initialize_repositories
    await initialize_repositories()
    
    yield
    # cleanup...
```

## 错误处理

所有Repository方法都会抛出`MilvusConnectionError`异常，需要在业务层捕获：

```python
from src.core.exceptions import MilvusConnectionError

try:
    results = await knowledge_repo.search(...)
except MilvusConnectionError as e:
    logger.error(f"Milvus查询失败: {e}")
    # 处理错误
```

## 迁移指南

### 从MilvusService迁移

```python
# ❌ 旧代码（已废弃）
from src.services.milvus_service import milvus_service
results = await milvus_service.search_knowledge(embedding, top_k=5)

# ✅ 新代码
from src.repositories import get_knowledge_repository
knowledge_repo = get_knowledge_repository()
results = await knowledge_repo.search(embedding, top_k=5)
```

**注意**: `MilvusService`已标记为`@deprecated`，将在0.3.0版本删除（2025-04-22）。

## 测试

使用Repository的mock fixtures：

```python
def test_knowledge_search(mock_knowledge_repository, mocker):
    from src.models.entities.knowledge import Knowledge
    
    mock_knowledge_repository.search.return_value = [
        Knowledge(text="测试", score=0.9, metadata={})
    ]
    
    with patch("src.repositories.get_knowledge_repository", 
               return_value=mock_knowledge_repository):
        # 测试代码
        ...
```

## 相关文档

- **ADR-0009**: [Repository模式重构决策](../../docs/adr/0009-repository-pattern-refactor.md)
- **Epic-004**: [统一数据访问层业务需求](../../docs/epics/epic-004-unified-data-access-layer.md)
- **Task File**: [Issue #64实施方案](../../project_document/proposals/issue-64-unified-data-access-layer.md)

## API参考

### BaseRepository

所有Repository的抽象基类，定义通用接口：

```python
class BaseRepository(ABC, Generic[T]):
    async def search(self, **kwargs) -> list[T]: ...
    async def insert(self, data: Any) -> int: ...
    async def delete(self, id: str) -> bool: ...
    async def count(self) -> int: ...
    async def health_check(self) -> bool: ...
```

### BaseMilvusRepository

Milvus特定的Repository基类，提供：

- `_get_milvus_client()`: 获取异步Milvus客户端
- `_create_collection()`: 创建Collection
- `_insert_data()`: 批量插入数据
- `_search_vectors()`: 向量搜索
- `_delete_by_id()`: 按ID删除
- `_count_entities()`: 统计实体数量
- `health_check()`: 健康检查

## 性能特点

- **异步I/O**: 基于`AsyncMilvusClient`，支持高并发
- **单例模式**: Repository实例全局唯一，避免重复初始化
- **懒加载**: Milvus客户端在首次使用时才创建连接
- **批量操作**: 支持批量插入，提升吞吐量

## 常见问题

### Q: Repository和MilvusService有什么区别？

**A**: Repository提供更高层次的抽象和类型安全：
- Repository返回强类型实体（`Knowledge`, `ConversationHistory`）
- MilvusService返回原始字典
- Repository支持泛型和IDE自动补全
- Repository设计支持未来扩展到关系数据库

### Q: 如何添加自定义查询逻辑？

**A**: 在具体的Repository子类中实现，利用`BaseMilvusRepository`的保护方法：

```python
class HistoryRepository(BaseMilvusRepository[ConversationHistory]):
    async def search_by_session(self, session_id: str, limit: int):
        client = await self._get_milvus_client()
        results = await client.query(
            collection_name=self.collection_name,
            expr=f'session_id == "{session_id}"',
            output_fields=["role", "text", "timestamp"],
            limit=limit,
        )
        # 客户端排序
        sorted_results = sorted(results, key=lambda x: x["timestamp"], reverse=True)
        return [ConversationHistory(**r) for r in sorted_results]
```

### Q: 如何在测试中使用Repository？

**A**: 使用`conftest.py`中的mock fixtures：

```python
# tests/conftest.py
@pytest.fixture
def mock_knowledge_repository(mocker):
    mock = mocker.AsyncMock()
    mock.search = mocker.AsyncMock(return_value=[])
    mock.insert = mocker.AsyncMock(return_value=0)
    return mock
```

---

**维护者**: LD Team  
**最后更新**: 2025-10-22  
**版本**: 1.0.0

