"""
FastAPI 应用入口

启动命令:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import AppException

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    启动时:
    - 初始化 PostgreSQL 连接（全局 DatabaseService）
    - 初始化 Milvus 连接
    - 初始化 Redis 连接
    - 创建 Milvus Collections（如果不存在）

    关闭时:
    - 关闭所有连接
    """
    logger.info("🚀 Starting Website Live Chat Agent...")
    logger.info(f"📊 LLM Provider: {settings.llm_provider}")
    logger.info(f"📊 LLM Model: {settings.llm_model_name}")
    logger.info(f"🗄️  Milvus Host: {settings.milvus_host}:{settings.milvus_port}")
    logger.info(f"💾 Redis Host: {settings.redis_host}:{settings.redis_port}")

    # 初始化全局 DatabaseService（防止连接泄漏）
    from src.db.base import DatabaseService
    db_service = DatabaseService(settings.postgres_url)
    app.state.db_service = db_service
    logger.info("✅ Global DatabaseService initialized")

    # 初始化 Milvus（测试环境可通过SKIP_MILVUS_INIT=1跳过）
    if not __import__("os").environ.get("SKIP_MILVUS_INIT"):
        try:
            from src.services.milvus_service import milvus_service
            await milvus_service.initialize()
            logger.info("✅ Milvus initialized successfully")

            # 初始化Repository层
            from src.repositories import initialize_repositories
            await initialize_repositories()
            logger.info("✅ Repositories initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Milvus: {e}")
            logger.warning("⚠️  Continuing without Milvus (some features will not work)")
    else:
        logger.info("⏭️  Skipping Milvus initialization (SKIP_MILVUS_INIT=1)")

    # 预编译 LangGraph App
    try:
        from src.agent.main.graph import get_agent_app
        agent_app = get_agent_app()
        logger.info("✅ LangGraph Agent compiled successfully")

        # 初始化 Redis Checkpointer 索引（如果使用 Redis checkpointer）
        if settings.langgraph_checkpointer == "redis" and hasattr(agent_app, 'checkpointer'):
            try:
                checkpointer = agent_app.checkpointer
                if hasattr(checkpointer, 'setup'):
                    await checkpointer.setup()
                    logger.info("✅ Redis Checkpointer indexes initialized successfully")
                else:
                    logger.info("ℹ️  Checkpointer has no setup method, indexes will be created on first use")
            except Exception as e:
                logger.warning(f"⚠️  Failed to setup Redis Checkpointer indexes: {e}")
                logger.warning("   Indexes will be created automatically on first use")
    except Exception as e:
        logger.error(f"❌ Failed to compile LangGraph Agent: {e}")

    yield

    # 清理资源
    logger.info("🛑 Shutting down Website Live Chat Agent...")

    # 关闭全局 DatabaseService
    try:
        if hasattr(app.state, 'db_service'):
            await app.state.db_service.close()
            logger.info("✅ Global DatabaseService closed")
    except Exception as e:
        logger.error(f"❌ Error closing DatabaseService: {e}")

    # 关闭 Milvus
    try:
        from src.services.milvus_service import milvus_service
        await milvus_service.close()
        logger.info("✅ Milvus closed")
    except Exception as e:
        logger.error(f"❌ Error closing Milvus: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title="Website Live Chat Agent API",
    description="基于 LangGraph + Milvus + DeepSeek 的智能客服 Agent",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException) -> JSONResponse:
    """处理自定义应用异常"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": exc.message,
                "type": "server_error",
                "code": exc.code,
            }
        },
    )


# 注册路由
# ruff: noqa: E402 - 导入必须在app创建后，避免循环依赖
from src.api.admin import analytics, auth, conversations, faq
from src.api.admin import knowledge as admin_knowledge
from src.api.admin import settings as admin_settings
from src.api.v1 import knowledge, openai_compat
from src.services.milvus_service import milvus_service

app.include_router(openai_compat.router, prefix="/v1", tags=["Chat"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["Knowledge"])

# 管理 API 路由
app.include_router(auth.router, tags=["Admin Auth"])
app.include_router(admin_knowledge.router, tags=["Admin Knowledge"])
app.include_router(conversations.router, tags=["Admin Conversations"])
app.include_router(analytics.router, tags=["Admin Analytics"])
app.include_router(admin_settings.router, tags=["Admin Settings"])
app.include_router(faq.router, tags=["Admin FAQ"])


# 健康检查端点
@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> dict:
    """健康检查"""
    milvus_healthy = await milvus_service.health_check()

    return {
        "status": "healthy" if milvus_healthy else "degraded",
        "services": {
            "milvus": {
                "status": "healthy" if milvus_healthy else "unhealthy",
                "host": settings.milvus_host,
            },
            "redis": {
                "status": "healthy",  # TODO: 实际检查 Redis
                "host": settings.redis_host,
            },
        },
        "timestamp": int(__import__("time").time()),
    }


# 根路径
@app.get("/", tags=["Root"])
async def root() -> dict:
    """API 根路径"""
    return {
        "message": "Website Live Chat Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model_name,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )

