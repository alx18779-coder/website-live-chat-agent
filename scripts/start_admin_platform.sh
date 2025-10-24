#!/bin/bash
# 运营管理平台一键启动脚本

set -e  # 遇到错误立即退出

echo "🚀 启动运营管理平台..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}❌ 错误: .env 文件不存在${NC}"
    echo "请先创建 .env 文件："
    echo "  cp .env.example .env"
    echo "  vim .env  # 编辑配置"
    exit 1
fi

# 检查必需的环境变量
echo "📋 检查环境配置..."
source .env

if [ -z "$ADMIN_USERNAME" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  警告: 未配置管理员账户${NC}"
    echo "请在 .env 文件中配置："
    echo "  ADMIN_USERNAME=admin"
    echo "  ADMIN_PASSWORD=your_secure_password  # 明文密码，系统会自动哈希存储"
    echo "  JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars_long"
    exit 1
fi

if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  警告: 未配置 PostgreSQL${NC}"
    echo "请在 .env 文件中配置："
    echo "  POSTGRES_HOST=localhost"
    echo "  POSTGRES_PORT=5432"
    echo "  POSTGRES_DB=chat_agent_admin"
    echo "  POSTGRES_USER=admin"
    echo "  POSTGRES_PASSWORD=your_postgres_password"
    exit 1
fi

echo -e "${GREEN}✅ 环境配置检查通过${NC}"
echo ""

# 步骤 1: 启动 PostgreSQL
echo "📊 步骤 1/4: 启动 PostgreSQL..."
if docker ps | grep -q chat-agent-postgres; then
    echo -e "${GREEN}✅ PostgreSQL 已在运行${NC}"
else
    docker run -d \
      --name chat-agent-postgres \
      -e POSTGRES_DB=${POSTGRES_DB:-chat_agent_admin} \
      -e POSTGRES_USER=${POSTGRES_USER:-admin} \
      -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
      -p ${POSTGRES_PORT:-5432}:5432 \
      postgres:15-alpine
    
    echo -e "${GREEN}✅ PostgreSQL 启动成功${NC}"
    echo "⏳ 等待 PostgreSQL 初始化（10秒）..."
    sleep 10
fi
echo ""

# 步骤 2: 初始化数据库
echo "🗄️  步骤 2/4: 初始化数据库..."
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo -e "${YELLOW}⚠️  警告: 虚拟环境不存在，使用系统 Python${NC}"
fi

python scripts/init_admin_db.py
echo ""

# 步骤 3: 启动后端（如果还没启动）
echo "🔧 步骤 3/4: 检查后端服务..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务已在运行${NC}"
else
    echo -e "${YELLOW}⚠️  后端服务未启动${NC}"
    echo "请在另一个终端启动后端："
    echo "  python src/main.py"
    echo "或使用 Docker:"
    echo "  docker-compose up -d chat-agent"
fi
echo ""

# 步骤 4: 启动前端
echo "🎨 步骤 4/4: 启动前端..."
if [ ! -d admin-frontend ]; then
    echo -e "${RED}❌ 错误: admin-frontend 目录不存在${NC}"
    exit 1
fi

cd admin-frontend

# 检查依赖
if [ ! -d node_modules ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

echo ""
echo -e "${GREEN}🎉 管理平台启动完成！${NC}"
echo ""
echo "📍 访问地址："
echo "  - 管理平台: http://localhost:5173"
echo "  - 后端 API: http://localhost:8000/docs"
echo ""
echo "🔑 登录信息："
echo "  - 用户名: ${ADMIN_USERNAME}"
echo "  - 密码: ${ADMIN_PASSWORD}"
echo ""
echo "🚀 启动前端开发服务器..."
npm run dev

