# 🚀 快速开始指南

10 分钟内启动您的智能客服 Agent！

## 📋 前置条件

- ✅ Python 3.13+
- ✅ DeepSeek API Key（或 OpenAI API Key）
- ✅ 已部署的 Milvus 服务
- ✅ Redis（可选，用于生产环境）

## 🛠️ 安装步骤

### 1️⃣ 克隆项目（如果需要）

```bash
cd /home/tian/Python/website-live-chat-agent
```

### 2️⃣ 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**必须修改的配置**：

```bash
# DeepSeek API Key（必填）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# Milvus 连接信息（必填）
MILVUS_HOST=192.168.1.100  # 改为你的 Milvus 地址
MILVUS_PORT=19530

# API 认证密钥（必填）
API_KEY=my-secure-api-key-12345  # 改为你的密钥
```

**可选配置**：

```bash
# Redis（如果没有 Redis，会自动使用内存模式）
REDIS_HOST=localhost
REDIS_PORT=6379

# 如果 Redis 不可用，改为内存模式
LANGGRAPH_CHECKPOINTER=memory
```

**管理平台配置**（可选，用于运营管理）：

```bash
# 管理员认证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars_long
JWT_EXPIRE_MINUTES=60

# PostgreSQL 数据库
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chat_agent_admin
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_postgres_password
```

### 3️⃣ 安装依赖

```bash
# 方式 1: 使用 uv（推荐，更快）
uv pip install -e .

# 方式 2: 使用 pip
pip install -e .
```

### 4️⃣ 启动服务

**⚠️ 重要**：直接运行 Python 需要先启动 Redis！

#### 方式 A：使用 Docker 启动 Redis（推荐）

```bash
# 1. 启动 Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# 2. 启动应用
python src/main.py

# 或使用 uvicorn（开发模式）
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### 方式 B：使用内存模式（无需 Redis）

```bash
# 1. 修改 .env 文件
echo "LANGGRAPH_CHECKPOINTER=memory" >> .env

# 2. 启动应用
python src/main.py
```

**注意**：内存模式下，对话状态在应用重启后会丢失。

**启动成功的标志**：

```
🚀 Starting Website Live Chat Agent...
📊 LLM Provider: deepseek
📊 LLM Model: deepseek-chat
🗄️  Milvus Host: 192.168.1.100:19530
💾 Redis Host: localhost:6379
✅ Connected to Milvus: 192.168.1.100:19530
✅ Milvus initialized successfully
✅ LangGraph Agent compiled successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5️⃣ 验证服务

打开浏览器访问：

- **Swagger UI**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

或使用 curl：

```bash
curl http://localhost:8000/api/v1/health
```

预期响应：

```json
{
  "status": "healthy",
  "services": {
    "milvus": {
      "status": "healthy",
      "host": "192.168.1.100"
    },
    "redis": {
      "status": "healthy",
      "host": "localhost"
    }
  },
  "timestamp": 1699999999
}
```

---

## 🎛️ 启动管理平台（可选）

管理平台提供 Web 界面用于监控和管理智能客服系统。

### 🚀 快速启动（推荐）

使用一键启动脚本：

```bash
# 确保已配置 .env 文件中的管理平台参数
./scripts/start_admin_platform.sh
```

脚本会自动：
1. ✅ 检查环境配置
2. ✅ 启动 PostgreSQL
3. ✅ 初始化数据库
4. ✅ 启动前端服务

### 📝 手动启动步骤

如果需要手动启动，按以下步骤操作：

#### 1️⃣ 启动 PostgreSQL

```bash
# 使用 Docker 启动 PostgreSQL
docker run -d \
  --name chat-agent-postgres \
  -e POSTGRES_DB=chat_agent_admin \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=your_postgres_password \
  -p 5432:5432 \
  postgres:15-alpine
```

### 2️⃣ 初始化数据库

```bash
# 激活虚拟环境（如果还没激活）
source .venv/bin/activate

# 运行数据库初始化脚本
python scripts/init_admin_db.py

# 验证数据库连接（可选）
python scripts/init_admin_db.py --check-only
```

**初始化成功的标志**：

```
🚀 开始初始化管理平台数据库...
📊 数据库配置: localhost:5432/chat_agent_admin
✅ 数据库连接已建立
📋 创建数据库表...
✅ 数据库表创建完成
👤 创建默认管理员账户...
✅ 管理员账户配置完成
🎉 数据库初始化完成！
```

### 3️⃣ 启动前端

```bash
# 进入前端目录
cd admin-frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

**启动成功的标志**：

```
VITE v7.1.12  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

### 4️⃣ 访问管理平台

打开浏览器访问：

- **管理平台**: http://localhost:5173
- **后端 API**: http://localhost:8000/docs

**默认登录信息**：
- 用户名: `admin`
- 密码: 在 `.env` 中配置的 `ADMIN_PASSWORD`

**管理平台功能**：
- 📊 仪表盘：总览统计和趋势分析
- 📚 知识库管理：查看、编辑、删除文档
- 📁 文件上传：支持 PDF、Markdown、纯文本文件上传和自动处理
- 💬 对话监控：查看用户对话历史
- 📈 统计报表：系统使用情况分析
- ⚙️ 系统配置：查看系统配置和健康状态

---

## 🎯 快速测试

### 1️⃣ 上传示例知识库

```bash
# 运行初始化脚本
python scripts/init_example_data.py
```

**注意**：修改脚本中的 `API_KEY` 变量为你在 `.env` 中设置的值。

### 2️⃣ 测试对话 API

**简单问候**：

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-secure-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": false
  }'
```

**知识库问答**（需先上传示例数据）：

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-secure-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "你们的退货政策是什么？"}
    ],
    "stream": false
  }'
```

**流式响应**：

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-secure-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "介绍一下你们的产品"}
    ],
    "stream": true
  }'
```

### 3️⃣ 测试知识库检索

```bash
curl "http://localhost:8000/api/v1/knowledge/search?query=退货政策&top_k=3" \
  -H "Authorization: Bearer my-secure-api-key-12345"
```

### 4️⃣ 测试文件上传功能

**上传文件到知识库**：

```bash
# 上传 PDF 文件
curl -X POST "http://localhost:8000/api/admin/knowledge/upload" \
  -H "Authorization: Bearer your-admin-token" \
  -F "files=@/path/to/your/document.pdf" \
  -F "source=官方文档" \
  -F "version=1.0"

# 上传 Markdown 文件
curl -X POST "http://localhost:8000/api/admin/knowledge/upload" \
  -H "Authorization: Bearer your-admin-token" \
  -F "files=@/path/to/your/document.md" \
  -F "source=用户手册" \
  -F "version=2.0"

# 批量上传多个文件
curl -X POST "http://localhost:8000/api/admin/knowledge/upload" \
  -H "Authorization: Bearer your-admin-token" \
  -F "files=@/path/to/file1.pdf" \
  -F "files=@/path/to/file2.md" \
  -F "files=@/path/to/file3.txt" \
  -F "source=批量上传" \
  -F "version=1.0"
```

**查看上传状态**：

```bash
# 获取上传记录列表
curl "http://localhost:8000/api/admin/knowledge/uploads" \
  -H "Authorization: Bearer your-admin-token"

# 获取特定上传的状态
curl "http://localhost:8000/api/admin/knowledge/uploads/{upload_id}" \
  -H "Authorization: Bearer your-admin-token"
```

**文件预览**：

```bash
# 预览文件内容（不保存）
curl -X POST "http://localhost:8000/api/admin/knowledge/preview" \
  -H "Authorization: Bearer your-admin-token" \
  -F "file=@/path/to/your/document.pdf"
```

**重试和回滚**：

```bash
# 重试失败的上传
curl -X POST "http://localhost:8000/api/admin/knowledge/uploads/{upload_id}/retry" \
  -H "Authorization: Bearer your-admin-token"

# 回滚上传（删除相关文档）
curl -X DELETE "http://localhost:8000/api/admin/knowledge/uploads/{upload_id}" \
  -H "Authorization: Bearer your-admin-token"
```

---

## 🐳 Docker 部署

### 使用 docker-compose（推荐，所有服务自动启动）

✅ **最简单的方式**：所有服务会自动启动，无需额外配置！

1. **编辑环境变量**：

```bash
# 创建 .env 文件
cp .env.example .env
vim .env  # 修改必填配置（DEEPSEEK_API_KEY, MILVUS_HOST, API_KEY）

# 如果需要管理平台，还需配置：
# ADMIN_USERNAME, ADMIN_PASSWORD, JWT_SECRET_KEY
# POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
```

2. **一键启动所有服务**：

```bash
docker-compose up -d
```

**启动的服务**：
- ✅ `chat-agent`（主应用，端口 8000）
- ✅ `redis`（缓存和状态存储）
- ✅ `postgres`（管理平台数据库，端口 5432）
- ✅ `admin-frontend`（管理平台前端，端口 3000）

3. **查看日志**：

```bash
# 查看所有服务
docker-compose logs -f

# 只查看应用日志
docker-compose logs -f chat-agent

# 只查看 Redis 日志
docker-compose logs -f redis
```

4. **停止服务**：

```bash
# 停止但保留数据
docker-compose down

# 停止并删除所有数据（包括 Redis）
docker-compose down -v
```

### 使用 Dockerfile（需要单独启动 Redis）

⚠️ **注意**：这种方式需要手动管理 Redis！

```bash
# 1. 创建 Docker 网络
docker network create chat-network

# 2. 启动 Redis
docker run -d \
  --name redis \
  --network chat-network \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes

# 3. 构建应用镜像
docker build -t chat-agent:latest .

# 4. 运行应用容器
docker run -d \
  --name chat-agent \
  --network chat-network \
  -p 8000:8000 \
  -e DEEPSEEK_API_KEY=sk-your-key \
  -e MILVUS_HOST=192.168.1.100 \
  -e REDIS_HOST=redis \
  -e API_KEY=my-api-key \
  chat-agent:latest

# 5. 查看日志
docker logs -f chat-agent
```

**或者使用内存模式**（无需 Redis）：

```bash
# 构建镜像
docker build -t chat-agent:latest .

# 运行容器（内存模式）
docker run -d \
  --name chat-agent \
  -p 8000:8000 \
  -e DEEPSEEK_API_KEY=sk-your-key \
  -e MILVUS_HOST=192.168.1.100 \
  -e API_KEY=my-api-key \
  -e LANGGRAPH_CHECKPOINTER=memory \
  chat-agent:latest
```

---

## 🔧 常见问题

### ❓ Milvus 连接失败

**错误信息**：
```
❌ Failed to connect to Milvus: ...
```

**解决方案**：
1. 检查 `MILVUS_HOST` 和 `MILVUS_PORT` 是否正确
2. 确认 Milvus 服务正在运行：
   ```bash
   telnet your-milvus-host 19530
   ```
3. 检查防火墙规则

### ❓ DeepSeek API Key 无效

**错误信息**：
```
DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek
```

**解决方案**：
1. 确认 `.env` 文件中 `DEEPSEEK_API_KEY` 已设置
2. 检查 API Key 格式（应以 `sk-` 开头）
3. 验证 API Key 有效性

### ❓ 端口已被占用

**错误信息**：
```
OSError: [Errno 98] Address already in use
```

**解决方案**：
1. 修改 `.env` 中的 `PORT=8001`
2. 或停止占用 8000 端口的进程：
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

### ❓ Redis 连接失败

**解决方案**：
1. 如果没有 Redis，改为内存模式：
   ```bash
   LANGGRAPH_CHECKPOINTER=memory
   ```
2. 或启动 Redis：
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

### ❓ PostgreSQL 连接失败

**错误信息**：
```
❌ 数据库连接失败: could not connect to server
```

**解决方案**：
1. 检查 PostgreSQL 是否启动：
   ```bash
   docker ps | grep postgres
   ```
2. 验证连接信息：
   ```bash
   # 测试连接
   docker exec -it chat-agent-postgres psql -U admin -d chat_agent_admin -c "SELECT 1;"
   ```
3. 检查 `.env` 中的配置是否正确

### ❓ 前端无法访问

**错误信息**：
```
Failed to fetch
```

**解决方案**：
1. 检查后端是否启动：
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
2. 检查前端配置：
   ```bash
   # 查看前端环境变量
   cat admin-frontend/.env
   
   # 应该包含：
   VITE_API_BASE_URL=http://localhost:8000
   ```
3. 重启前端服务：
   ```bash
   cd admin-frontend
   npm run dev
   ```

### ❓ 管理员登录失败

**错误信息**：
```
Invalid credentials
```

**解决方案**：
1. 检查 `.env` 中的管理员配置：
   ```bash
   grep ADMIN .env
   ```
2. 确认密码是否正确（区分大小写）
3. 重新初始化数据库：
   ```bash
   python scripts/init_admin_db.py
   ```

### ❓ 数据库初始化失败

**错误信息**：
```
sqlalchemy.exc.OperationalError
```

**解决方案**：
1. 确保 PostgreSQL 已启动并等待 30 秒
2. 检查数据库连接参数
3. 查看详细错误日志：
   ```bash
   python scripts/init_admin_db.py 2>&1 | tee init.log
   ```
4. 如果表已存在，可以删除重建：
   ```bash
   docker exec -it chat-agent-postgres psql -U admin -d chat_agent_admin -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   python scripts/init_admin_db.py
   ```

---

## 📖 下一步

- 📚 阅读 [README.md](README.md) 了解完整功能
- 🏗️ 查看 [ADR 文档](docs/adr/) 了解架构设计
- 🎛️ 查看 [管理平台部署指南](docs/deployment/admin-platform.md)
- 📖 阅读 [管理平台用户手册](docs/user-guide/admin-platform.md)
- 🔌 参考 WordPress 集成指南（README 中）
- 🧪 运行测试：`pytest`

---

## 💡 提示

1. **开发模式**：使用 `--reload` 参数自动重载代码
2. **调试日志**：设置 `LOG_LEVEL=DEBUG` 查看详细日志
3. **API 文档**：访问 `/docs` 查看所有可用端点
4. **监控 Milvus**：定期检查 Collection 大小和索引状态
5. **管理平台**：使用管理平台可视化监控系统运行状态
6. **数据备份**：定期备份 PostgreSQL 数据库（对话历史和审计日志）
7. **安全建议**：生产环境务必修改默认密码和 JWT 密钥
8. **文件上传**：支持 PDF、Markdown、纯文本格式，单文件最大 10MB
9. **文件处理**：上传的文件会自动解析、分块、生成向量并存储到 Milvus
10. **上传监控**：通过管理平台可以查看上传进度、重试失败任务、回滚上传

---

**遇到问题？** 查看完整日志：

```bash
# 应用日志
tail -f logs/app.log

# Docker 日志
docker-compose logs -f

# 或查看完整 README
cat README.md
```

---

**🎉 祝您使用愉快！**

