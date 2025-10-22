# ADR-0009: Repository模式重构 - 统一数据访问层

**状态**: Accepted  
**日期**: 2025-10-22  
**决策者**: AR (Architect AI)  
**相关文档**: 
- Epic-004: [docs/epics/epic-004-unified-data-access-layer.md](../epics/epic-004-unified-data-access-layer.md)
- Issue: [#64](https://github.com/alx18779-coder/website-live-chat-agent/issues/64)
- Task File: [project_document/proposals/issue-64-unified-data-access-layer.md](../../project_document/proposals/issue-64-unified-data-access-layer.md)

---

## Context (背景)

### 问题陈述

当前系统采用集中式`MilvusService`管理所有collection，存在以下问题：

1. **代码重复严重**: 每个collection需要专门的search/insert方法
2. **扩展成本高**: 添加新collection需要1-2天，编写100+行重复代码
3. **维护困难**: 多处修改同步，容易遗漏
4. **不符合开闭原则**: 对扩展不开放，对修改不封闭

**业务影响**:
- 新功能开发周期长
- 代码质量下降（复制粘贴）
- 无法快速响应业务需求

### 需求

**PM需求** (来自Epic-004):
- 添加新数据源从2天缩短到2小时（**效率提升70%**）
- 减少重复代码50%
- 统一的数据访问接口

---

## Decision (决策)

采用**混合Repository模式**重构数据访问层：

### 核心架构

```
抽象层: BaseRepository (统一接口)
  ↓
实现层: BaseMilvusRepository (Milvus通用CRUD)
  ↓
应用层: KnowledgeRepository, HistoryRepository (类型封装)
```

### 关键设计决策

#### 1. 采用混合Repository模式

**选择原因**:
- 平衡代码复用和类型安全
- 符合项目Pydantic风格
- 新增collection只需10-20行代码

**备选方案对比**:

| 方案 | 类型安全 | 代码复用 | 新增代码量 | 结论 |
|-----|---------|---------|-----------|------|
| 纯Repository | ✅ 最强 | ❌ 差 | 100+行 | ❌ 重复严重 |
| 通用Manager | ❌ 无（dict） | ✅ 好 | 5行配置 | ❌ 不符合项目风格 |
| **混合模式** | ✅ 强 | ✅ 好 | 10-20行 | ✅ **采用** |

#### 2. Schema定义在Python代码

使用Pydantic BaseModel定义schema，**不使用**配置文件。

**理由**:
- 类型安全 + IDE支持
- 符合项目现有风格
- 编译时检查

#### 3. 完全重构，废弃旧接口

保留`MilvusService`作为facade（标记@deprecated），新代码使用Repository。

**理由**:
- 清晰的架构边界
- 渐进式迁移（降低风险）
- 向后兼容

#### 4. 预留关系数据库接口

创建`src/repositories/relational/`目录。

**理由**:
- 支持未来扩展
- 统一的抽象层

---

## Consequences (后果)

### ✅ 正面影响

#### 1. 开发效率大幅提升

**现在**: 添加FAQ库
```python
# 只需10-20行代码（2小时）
class FAQRepository(BaseMilvusRepository[FAQ]):
    async def search(self, embedding, top_k) -> list[FAQ]:
        results = await self._base_search(embedding, top_k)
        return [FAQ(**r) for r in results]
```

**之前**: 需要100+行代码（2天）
- 复制粘贴schema定义
- 重写search/insert逻辑
- 更新多个调用方

#### 2. 代码质量提升

- **重复代码减少50%**: 通用逻辑在基类
- **类型安全**: Pydantic模型 + IDE支持
- **易于测试**: 可Mock基类

#### 3. 架构清晰

- 清晰的分层（抽象-实现-应用）
- 符合SOLID原则
- 易于扩展

### ⚠️ 负面影响与风险

#### 风险1: 向后兼容性破坏 🟡 中

**描述**: API调用方式变更可能影响现有功能

**缓解措施**:
1. 保留`MilvusService`作为facade
2. 渐进式迁移（分Phase实施）
3. 充分的单元测试和集成测试

#### 风险2: 性能回归 🟡 中

**描述**: 抽象层可能引入性能开销

**缓解措施**:
1. 基准测试对比（性能不低于现有）
2. 优化关键路径
3. 异步架构保持（基于ADR-0008）

#### 风险3: 学习曲线 🟢 低

**描述**: 新成员需要理解Repository模式

**缓解措施**:
1. 详细文档和示例
2. 清晰的目录结构
3. IDE类型提示

#### 风险4: 测试覆盖不足 🟡 中

**描述**: 重构可能遗漏边缘场景

**缓解措施**:
1. 保持测试覆盖率≥80%
2. 保留现有测试作为回归测试
3. 新增Repository专项测试

### ⚙️ 技术债务

| 债务项 | 优先级 | 说明 |
|-------|-------|------|
| 旧MilvusService清理 | P2 | 6个月后删除deprecated代码 |
| 关系数据库实现 | P2 | 需求明确时再实现 |
| 连接池优化 | P2 | 根据性能测试决定 |

---

## 技术约束与架构原则

### P0约束（必须遵守）

1. **向后兼容**: 保留旧API，标记deprecated
2. **性能要求**: 查询延迟不高于现有实现
3. **类型安全**: 全量使用Pydantic模型
4. **测试覆盖**: ≥80%覆盖率

### P1约束（强烈建议）

1. **代码质量**: 通过ruff和mypy检查
2. **文档完整**: Docstring + README + ADR
3. **错误处理**: 统一异常类型和日志

### P2约束（可选）

1. **可观测性**: 性能指标收集
2. **扩展性**: 支持自定义Repository

---

## 验证标准

### 功能验证

- [ ] 现有知识库和对话历史功能正常
- [ ] 提供新collection添加示例（FAQ）
- [ ] 所有API端点正常工作

### 质量验证

- [ ] 单元测试覆盖率≥80%
- [ ] 集成测试通过（并发场景）
- [ ] 性能基准测试：延迟≤现有实现

### 业务价值验证

- [ ] 添加FAQ库实测：≤2小时
- [ ] 代码行数对比：减少≥50%
- [ ] 团队满意度：≥4/5分

---

## 实施计划

详见Task File: `project_document/proposals/issue-64-unified-data-access-layer.md`

**核心步骤**:

1. **Phase 1**: 基础架构（4-5h）
   - Schema定义
   - 数据实体
   
2. **Phase 2**: Repository实现（6-8h）
   - 基类实现
   - Knowledge/History Repository
   
3. **Phase 3**: 迁移与集成（4-5h）
   - 更新调用方
   - 测试更新
   
4. **Phase 4**: 文档与清理（2h）
   - README更新
   - 标记deprecated

**预估总工作量**: 16-20小时

---

## 相关决策

- **ADR-0001**: LangGraph架构 - 无冲突，数据访问层独立
- **ADR-0002**: Milvus集成设计 - 需更新实现章节，设计理念不变
- **ADR-0008**: Milvus异步重构 - 本ADR是ADR-0008的深化，继承异步架构

---

## 参考资料

1. **Epic-004**: 业务需求文档
2. **Task File**: 完整的技术分析和方案对比
3. **现有代码**: `src/services/milvus_service.py`（355行，需重构）
4. **Repository模式**: [Martin Fowler - Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

---

**变更历史**:

| 日期 | 版本 | 变更内容 | 负责人 |
|---|---|---|-----|
| 2025-10-22 | 1.0 | 初始版本 - 架构决策完成 | AR AI |

