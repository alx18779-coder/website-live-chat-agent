# 运营管理平台部署指南

## 概述

本文档介绍如何部署和配置运营管理平台，包括后端 API、前端界面和数据库服务。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin UI      │    │   Chat Agent    │    │   PostgreSQL   │
│   (Vue 3)       │◄───┤   (FastAPI)     │◄───┤   (Database)    │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │     Redis       │    │     Milvus      │
│   (Frontend)    │    │   (Cache)       │    │   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 环境要求

### 硬件要求
- CPU: 2 核心以上
- 内存: 4GB 以上
- 存储: 20GB 以上可用空间

### 软件要求
- Docker: 20.10+
- Docker Compose: 2.0+
- Git: 2.0+

## 快速部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd website-live-chat-agent
```

### 2. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```bash
# ==================== 管理员认证配置 ====================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars_long
JWT_EXPIRE_MINUTES=60

# ==================== PostgreSQL 配置 ====================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chat_agent_admin
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_postgres_password

# ==================== 其他配置 ====================
# LLM 配置
DEEPSEEK_API_KEY=your_deepseek_api_key
# Milvus 配置
MILVUS_HOST=your_milvus_host
MILVUS_PORT=19530
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 初始化数据库

```bash
# 等待 PostgreSQL 启动
sleep 30

# 初始化数据库
python scripts/init_admin_db.py

# 或者仅检查连接
python scripts/init_admin_db.py --check-only
```

### 5. 访问管理平台

- **管理平台**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

默认登录信息：
- 用户名: `admin`
- 密码: 在 `.env` 文件中配置的 `ADMIN_PASSWORD`

## 详细配置

### 环境变量说明

#### 管理员认证配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ADMIN_USERNAME` | `admin` | 管理员用户名 |
| `ADMIN_PASSWORD` | - | 管理员密码（必须设置） |
| `JWT_SECRET_KEY` | - | JWT 密钥（必须设置，至少32字符） |
| `JWT_EXPIRE_MINUTES` | `60` | JWT 过期时间（分钟） |

#### PostgreSQL 配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `POSTGRES_HOST` | `localhost` | PostgreSQL 主机 |
| `POSTGRES_PORT` | `5432` | PostgreSQL 端口 |
| `POSTGRES_DB` | `chat_agent_admin` | 数据库名 |
| `POSTGRES_USER` | `admin` | 数据库用户名 |
| `POSTGRES_PASSWORD` | - | 数据库密码（必须设置） |

#### 前端配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | API 基础 URL |

### 数据库初始化

数据库初始化脚本 `scripts/init_admin_db.py` 会执行以下操作：

1. **创建表结构**: 自动创建所有必需的数据表
2. **验证连接**: 确保数据库连接正常
3. **配置管理员**: 设置默认管理员账户

```bash
# 完整初始化
python scripts/init_admin_db.py

# 仅检查连接
python scripts/init_admin_db.py --check-only
```

### 服务管理

#### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d postgres
docker-compose up -d chat-agent
docker-compose up -d admin-frontend
```

#### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

#### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f chat-agent
docker-compose logs -f admin-frontend
docker-compose logs -f postgres
```

#### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart chat-agent
```

## 生产环境部署

### 安全配置

1. **修改默认密码**:
   ```bash
   # 生成强密码
   openssl rand -base64 32
   
   # 更新 .env 文件
   ADMIN_PASSWORD=your_very_secure_password
   POSTGRES_PASSWORD=your_very_secure_postgres_password
   JWT_SECRET_KEY=your_very_secure_jwt_secret_key
   ```

2. **配置防火墙**:
   ```bash
   # 只开放必要端口
   ufw allow 3000  # 管理平台
   ufw allow 8000  # API（如果需要外部访问）
   ufw deny 5432   # PostgreSQL（仅内部访问）
   ```

3. **使用 HTTPS**:
   - 配置 Nginx SSL 证书
   - 更新前端 API 基础 URL

### 性能优化

1. **数据库优化**:
   ```bash
   # PostgreSQL 配置优化
   # 在 docker-compose.yml 中添加：
   command: postgres -c shared_buffers=256MB -c max_connections=200
   ```

2. **Redis 配置**:
   ```bash
   # Redis 内存优化
   # 在 docker-compose.yml 中添加：
   command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

3. **前端优化**:
   - 启用 Gzip 压缩
   - 配置静态资源缓存
   - 使用 CDN 加速

### 监控和日志

1. **健康检查**:
   ```bash
   # 检查服务状态
   curl http://localhost:8000/api/v1/health
   curl http://localhost:3000/health
   ```

2. **日志收集**:
   ```bash
   # 配置日志轮转
   docker-compose logs --tail=1000 -f > logs/app.log
   ```

3. **性能监控**:
   - 使用 Prometheus + Grafana
   - 监控数据库性能
   - 监控 API 响应时间

## 故障排除

### 常见问题

#### 1. 数据库连接失败

**症状**: 应用启动失败，日志显示数据库连接错误

**解决方案**:
```bash
# 检查 PostgreSQL 是否启动
docker-compose ps postgres

# 检查数据库日志
docker-compose logs postgres

# 手动测试连接
docker-compose exec postgres psql -U admin -d chat_agent_admin -c "SELECT 1;"
```

#### 2. 前端无法访问 API

**症状**: 前端页面加载，但 API 请求失败

**解决方案**:
```bash
# 检查 API 服务状态
curl http://localhost:8000/api/v1/health

# 检查网络连接
docker-compose exec admin-frontend ping chat-agent

# 检查 Nginx 配置
docker-compose exec admin-frontend cat /etc/nginx/conf.d/default.conf
```

#### 3. 认证失败

**症状**: 无法登录管理平台

**解决方案**:
```bash
# 检查 JWT 配置
echo $JWT_SECRET_KEY

# 重新初始化数据库
python scripts/init_admin_db.py

# 检查管理员账户
docker-compose exec postgres psql -U admin -d chat_agent_admin -c "SELECT * FROM admin_audit_log LIMIT 5;"
```

#### 4. 内存不足

**症状**: 服务频繁重启或响应缓慢

**解决方案**:
```bash
# 检查内存使用
docker stats

# 优化配置
# 减少 PostgreSQL 共享缓冲区
# 限制 Redis 内存使用
# 优化 Docker 资源限制
```

### 日志分析

#### 查看错误日志

```bash
# 查看所有错误
docker-compose logs | grep -i error

# 查看特定服务错误
docker-compose logs chat-agent | grep -i error
docker-compose logs admin-frontend | grep -i error
```

#### 性能分析

```bash
# 查看慢查询
docker-compose exec postgres psql -U admin -d chat_agent_admin -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

## 备份和恢复

### 数据库备份

```bash
# 创建备份
docker-compose exec postgres pg_dump -U admin chat_agent_admin > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker-compose exec -T postgres psql -U admin chat_agent_admin < backup_file.sql
```

### 配置备份

```bash
# 备份环境配置
cp .env .env.backup

# 备份 Docker Compose 配置
cp docker-compose.yml docker-compose.yml.backup
```

## 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 数据库迁移

```bash
# 运行数据库迁移
docker-compose exec chat-agent alembic upgrade head

# 检查迁移状态
docker-compose exec chat-agent alembic current
```

### 清理和维护

```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的卷
docker volume prune -f

# 清理日志文件
docker-compose logs --tail=0
```

## 联系支持

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目 GitHub Issues
3. 联系技术支持团队

---

**注意**: 在生产环境中部署前，请务必：
- 修改所有默认密码
- 配置适当的防火墙规则
- 设置定期备份
- 监控系统性能
