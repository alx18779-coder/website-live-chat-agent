# ADR-0010: 运营管理平台架构设计

**状态**: 已接受  
**日期**: 2025-10-24  
**决策者**: AR (Architect AI), PM (Product Manager AI)  
**相关文档**: [Epic-005](../epics/epic-005-operations-management-platform.md), [Task File](../../project_document/proposals/epic-005-operations-management-platform.md)

---

## Context (背景)

### 业务需求
当前智能客服系统虽然提供了完整的API接口，但缺乏可视化管理界面，导致运营人员在日常维护中面临以下痛点：

1. **知识库管理困难**：需要通过curl命令或Postman调用API上传、修改、删除知识库文档，操作复杂且容易出错
2. **对话质量无法监控**：无法直观查看历史对话记录，难以评估AI回答质量和发现知识库盲区
3. **缺乏数据洞察**：没有统计报表，无法了解系统使用情况，难以做出数据驱动的优化决策
4. **运营效率低下**：简单的知识库维护工作需要花费大量时间，学习成本高

### 技术背景
- 现有系统基于LangGraph + Milvus + Redis架构
- 已有完整的API接口（`/v1/*`）
- 需要保持向后兼容性
- 目标用户：1-5人的小团队管理员

---

## Decision (决策)

**采用前后端分离的管理平台架构**，通过引入PostgreSQL存储对话历史，构建Vue 3前端界面，实现知识库可视化管理、对话监控、统计报表、系统配置四大核心功能。

**核心实现**：
1. **后端扩展**：新增`/api/admin/*`路由，实现管理员认证、知识库管理、对话监控、统计报表API
2. **数据存储**：引入PostgreSQL存储对话历史，保持Milvus向量检索不变
3. **前端界面**：Vue 3 + TypeScript + Naive UI构建现代化管理界面
4. **认证安全**：JWT token + bcrypt密码哈希，单一管理员账户
5. **部署方式**：Docker Compose统一部署，Nginx反向代理

---

## Consequences (后果)

### ⚠️ 负面影响与风险

#### 🔴 高风险：数据同步风险

**风险场景1：对话历史同步失败**
- **问题**：用户对话数据存储在Redis中，需要异步同步到PostgreSQL供管理界面查询
- **影响**：管理界面显示的历史对话不完整，统计数据不准确
- **表现**：今日会话量显示100次，实际Redis中有120次会话

**风险场景2：知识库更新不一致**
- **问题**：管理员通过界面更新知识库时，需要同时更新Milvus向量和PostgreSQL元数据
- **影响**：检索结果可能不准确，管理界面显示的信息与实际不符
- **表现**：界面显示文档已更新，但AI检索时仍使用旧版本

**影响范围**：统计报表功能、知识库管理功能、对话监控功能

**缓解措施**：
- **实时同步**：每次对话完成后异步触发Redis→PostgreSQL同步
- **定时同步**：每日凌晨2点全量同步检查，修复不一致数据
- **错误处理**：指数退避重试（最多3次），失败数据进入死信队列
- **监控告警**：同步失败率>5%时发送告警，提供手动修复接口
- **分布式事务**：知识库更新时确保Milvus和PostgreSQL一致性
- 实现数据同步状态API，实时监控同步健康度

#### 🔴 高风险：性能影响风险
**风险描述**：新增PostgreSQL查询可能影响整体系统性能
**影响范围**：系统响应时间
**缓解措施**：
- 使用数据库连接池（pool_size=10）
- 实现查询缓存机制（Redis缓存5分钟）
- 异步数据同步，不阻塞主API
- 数据库查询优化和索引

#### 🔴 高风险：安全风险
**风险描述**：管理员认证被绕过，导致数据泄露
**影响范围**：整个系统安全
**缓解措施**：
- 强密码策略（bcrypt哈希）
- JWT token过期机制（1小时）
- 操作审计日志
- 敏感信息脱敏显示

#### 🟡 中风险：部署复杂度增加
**风险描述**：新增PostgreSQL和前端服务，部署配置复杂化
**影响范围**：运维成本
**缓解措施**：
- 提供完整Docker Compose配置
- 编写详细部署文档
- 提供一键部署脚本
- 环境变量统一配置

#### 🟡 中风险：前端技术栈学习成本
**风险描述**：团队需要学习Vue 3 + TypeScript
**影响范围**：开发效率
**缓解措施**：
- 选择成熟UI组件库（Naive UI）
- 提供代码模板和最佳实践
- 分阶段实施
- 详细技术文档

### ✅ 正面影响

#### 1. 运营效率大幅提升
- **知识库管理效率提升80%**：从平均15分钟（使用API）降低到3分钟（使用Web界面）
- **学习成本降低**：无需学习API调用和命令行操作，新员工可快速上手
- **错误率降低**：可视化操作减少人为错误，避免误删重要文档

#### 2. 服务质量提升
- **实时监控对话质量**：及时发现AI回答不佳的情况，快速优化
- **快速发现知识库盲区**：通过对话记录发现用户常问但知识库缺失的内容
- **持续改进机制**：基于数据反馈不断优化知识库内容

#### 3. 数据驱动决策
- **了解系统运营状况**：通过统计数据了解用户使用习惯和系统表现
- **支持优化决策**：基于高频问题和命中率数据，优先优化重要内容
- **量化改进效果**：通过趋势图直观看到优化效果

### ⚙️ 技术债务

#### 1. 数据同步复杂性
- **问题**：需要维护Redis、PostgreSQL、Milvus三套数据的一致性
- **成本**：增加数据同步逻辑，需要处理同步失败场景
- **缓解**：异步同步，失败重试机制，数据修复工具

#### 2. 部署复杂度
- **问题**：从单服务扩展到多服务（PostgreSQL、前端、Nginx）
- **成本**：运维复杂度增加，需要监控多个服务
- **缓解**：Docker Compose统一管理，健康检查，监控告警

#### 3. 前端维护成本
- **问题**：新增前端技术栈，需要维护Vue 3项目
- **成本**：前端依赖更新，安全漏洞修复
- **缓解**：选择稳定技术栈，定期更新，自动化构建

---

## 技术约束与架构原则

### P0约束（必须遵守）

#### 1. 向后兼容性
- ✅ 现有API接口（`/v1/*`）完全保持兼容
- ✅ 现有配置项不能删除或修改
- ✅ 现有数据格式不能改变
- ✅ 现有功能不受影响

#### 2. 数据安全
- ✅ 管理员密码使用bcrypt哈希存储（至少8位，包含字母数字）
- ✅ JWT token设置合理过期时间（1小时），支持续签机制
- ✅ 敏感配置信息脱敏显示（API Key显示前4位+后4位）
- ✅ 所有管理API需要认证，记录审计日志（保留30天）
- ✅ 无IP白名单（MVP阶段），单一管理员账户

#### 3. 性能要求
- ✅ 管理界面响应时间<2秒（P95）
- ✅ 支持1000+文档的流畅浏览
- ✅ 不影响现有API性能
- ✅ 数据库查询优化
- ✅ 数据同步延迟<30秒
- ✅ API响应时间<500ms

#### 4. 多环境部署
- ✅ 开发环境：本地Docker Compose，共享Milvus
- ✅ 预发环境：独立PostgreSQL，共享Milvus  
- ✅ 生产环境：独立PostgreSQL + Milvus
- ✅ PostgreSQL版本≥13，内存≥2GB
- ✅ 前端Nginx配置，静态资源CDN

### P1约束（强烈建议）

#### 1. 代码质量
- ✅ 新增代码通过类型检查（mypy）
- ✅ 编写单元测试（覆盖率>80%）
- ✅ 遵循现有代码风格
- ✅ 添加适当注释

#### 2. 文档完整性
- ✅ 提供用户操作手册
- ✅ 提供API文档
- ✅ 提供部署指南
- ✅ 更新README.md

### P2约束（可选）

#### 1. 扩展性
- ✅ 预留多管理员账户接口
- ✅ 预留权限管理接口
- ✅ 预留审计日志接口
- ✅ 预留实时推送接口

---

## 验证标准

### 功能验证
- [ ] 管理员可以登录系统
- [ ] 知识库文档可以查看、搜索、编辑、删除
- [ ] 对话历史可以查询和查看详情
- [ ] 统计报表显示正确的数据
- [ ] 系统配置可以查看和更新
- [ ] 所有操作有明确的成功/失败反馈

### 质量验证
- [ ] 页面加载时间<2秒
- [ ] 支持1000+文档的流畅浏览
- [ ] 系统运行稳定，无崩溃
- [ ] 错误处理完善
- [ ] 数据一致性保证

### 业务价值验证
- [ ] 知识库管理时间从15分钟降低到3分钟（通过操作时间埋点统计）
- [ ] 100%历史对话可查询（数据同步一致性检查）
- [ ] 管理员操作满意度达到4星以上（满意度调查，≥5个有效评分）
- [ ] 上线后7天内，管理员日均使用≥3次（使用频率统计）

### 技术指标验证
- [ ] 数据同步成功率≥95%（监控端点统计）
- [ ] 同步延迟<30秒（实时监控）
- [ ] 页面加载时间<2秒（P95，前端埋点）
- [ ] API响应时间<500ms（后端监控）
- [ ] 数据一致性检查通过（定时任务验证）

---

## 体系结构视图

### 部署拓扑图
![运营管理平台架构图](../architecture/operations-management-platform-architecture.drawio)

**架构组件说明**：
- **前端层**：Nginx反向代理 + Vue 3管理界面
- **API层**：FastAPI管理API + 主API（/v1/*）
- **数据层**：Redis（会话缓存）+ PostgreSQL（对话历史）+ Milvus（向量检索）
- **数据流**：管理员 → Nginx → 前端 → 管理API → PostgreSQL/Milvus

### 数据同步流程图
![数据同步流程图](../architecture/data-sync-flow.drawio)

**数据流说明**：
1. **用户对话** → LangGraph Agent → Redis（会话状态）
2. **异步同步**：Redis → 同步服务 → PostgreSQL（对话历史）
3. **管理查询**：管理界面 → PostgreSQL（历史查询）
4. **监控告警**：同步服务 → 监控系统（状态跟踪）

### 关键数据流
- **实时流**：用户对话 → Redis → 异步同步 → PostgreSQL
- **查询流**：管理界面 → 管理API → PostgreSQL/Milvus
- **监控流**：同步服务 → 监控系统 → 告警通知

---

## 契约/接口变更声明

### 新增API接口

#### 管理认证接口
```yaml
/api/admin/auth/login:
  POST:
    request: { username: string, password: string }
    response: { access_token: string, token_type: "bearer", expires_in: number }

/api/admin/auth/refresh:
  POST:
    request: { refresh_token: string }
    response: { access_token: string, expires_in: number }
```

#### 知识库管理接口
```yaml
/api/admin/knowledge/documents:
  GET: # 分页查询文档列表
  POST: # 创建新文档
  
/api/admin/knowledge/documents/{doc_id}:
  GET: # 获取文档详情
  PUT: # 更新文档
  DELETE: # 删除文档
```

#### 对话监控接口
```yaml
/api/admin/conversations/history:
  GET: # 查询历史会话列表
  
/api/admin/conversations/{session_id}:
  GET: # 获取会话详情
```

#### 统计报表接口
```yaml
/api/admin/analytics/overview:
  GET: # 获取总览统计
  
/api/admin/analytics/trends:
  GET: # 获取趋势分析
```

#### 系统配置接口
```yaml
/api/admin/settings:
  GET: # 获取系统配置（脱敏）
  
/api/admin/settings/health:
  GET: # 系统健康检查
```

#### 数据同步接口
```yaml
/api/admin/sync/status:
  GET: # 同步状态查询
  
/api/admin/sync/metrics:
  GET: # 同步指标统计
  
/api/admin/sync/repair:
  POST: # 手动修复不一致数据
```

### 配置文件变更

#### 环境变量新增
```bash
# 管理员认证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_key
JWT_EXPIRE_MINUTES=60

# PostgreSQL配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chat_agent_admin
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_postgres_password
```

#### Docker Compose新增服务
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

  admin-frontend:
    build: ./admin-frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_BASE_URL=http://chat-agent:8000/api/admin
```

### 监控端点新增

#### 健康检查端点
```yaml
/api/admin/health:
  GET:
    response: {
      status: "healthy" | "degraded",
      services: {
        milvus: { status: "healthy" | "unhealthy" },
        redis: { status: "healthy" | "unhealthy" },
        postgres: { status: "healthy" | "unhealthy" }
      }
    }
```

#### 指标监控端点
```yaml
/api/admin/metrics:
  GET:
    response: {
      sync_success_rate: number,
      sync_latency_ms: number,
      api_response_time_ms: number,
      active_sessions: number
    }
```

### 事件总线变更

#### 新增事件类型
```typescript
// 数据同步事件
interface SyncEvent {
  type: 'conversation_synced' | 'sync_failed' | 'sync_repaired';
  session_id: string;
  timestamp: number;
  success: boolean;
  error?: string;
}

// 管理操作事件
interface AdminActionEvent {
  type: 'admin_login' | 'document_created' | 'document_updated' | 'document_deleted';
  admin_user: string;
  resource_id?: string;
  timestamp: number;
}
```

### 数据库Schema变更

#### PostgreSQL新增表
```sql
-- 对话历史表
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    user_message TEXT,
    ai_response TEXT,
    retrieved_docs JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 管理操作审计表
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY,
    admin_user VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id UUID,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 责任人分配

| 变更类型 | 责任人 | 交付物 | 完成时间 |
|---------|--------|--------|----------|
| API接口设计 | LD | OpenAPI规范 | Day 3 |
| 数据库Schema | LD | Alembic迁移脚本 | Day 2 |
| 前端接口调用 | LD | API客户端封装 | Day 6 |
| 监控端点实现 | LD | 健康检查API | Day 4 |
| 配置文件更新 | LD | 环境变量文档 | Day 2 |
| 部署配置 | LD | Docker Compose更新 | Day 8 |

---

## 相关决策

- [ADR-0001: LangGraph架构](./0001-langgraph-architecture.md) - 保持Agent工作流不变
- [ADR-0002: Milvus集成设计](./0002-milvus-integration.md) - 保持向量检索不变，管理界面扩展Repository方法
- [ADR-0003: 模型别名策略](./0003-model-alias-strategy.md) - 管理界面可查看配置
- [ADR-0004: Milvus索引配置修复](./0004-milvus-index-fix.md) - 确保Milvus服务稳定运行
- [ADR-0005: 模型配置分离](./0005-model-configuration-separation.md) - 管理界面可查看LLM和Embedding配置
- [ADR-0008: Milvus服务异步化重构](./0008-milvus-async-refactor.md) - 使用异步API，支持管理界面的并发查询
- [ADR-0009: Repository模式重构](./0009-repository-pattern-refactor.md) - 统一数据访问层，简化管理界面数据操作

---

## 参考资料

- [Epic-005: 运营管理平台](../epics/epic-005-operations-management-platform.md)
- [Task File: 详细实施计划](../../project_document/proposals/epic-005-operations-management-platform.md)
- [Vue 3官方文档](https://vuejs.org/)
- [Naive UI组件库](https://www.naiveui.com/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)

---

**变更历史**:

| 日期 | 版本 | 变更内容 | 负责人 |
|------|------|---------|--------|
| 2025-10-24 | 1.0 | 初始版本，确定运营管理平台架构 | AR AI |
