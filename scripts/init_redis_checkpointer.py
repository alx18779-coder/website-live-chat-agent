"""
初始化 LangGraph Redis Checkpointer 索引

这个脚本会连接到 Redis 并为 LangGraph 的 AsyncRedisSaver 创建必要的索引。

使用方法:
    python scripts/init_redis_checkpointer.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_redis_checkpointer():
    """初始化 Redis Checkpointer 索引"""
    try:
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver
        
        # 构建 Redis 连接 URL
        redis_url = "redis://"
        if settings.redis_password:
            redis_url += f":{settings.redis_password}@"
        redis_url += f"{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        
        logger.info(f"🔗 Connecting to Redis: {settings.redis_host}:{settings.redis_port}")
        
        # 首先测试 Redis 基本连接
        import redis.asyncio as redis
        redis_client = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # 测试 ping
        await redis_client.ping()
        logger.info("✅ Redis connection successful")
        
        # 检查 RediSearch 模块
        modules = await redis_client.execute_command("MODULE LIST")
        has_search = any("search" in str(m).lower() for m in modules) if modules else False
        
        if not has_search:
            logger.error("❌ RediSearch module not found!")
            logger.error("   LangGraph AsyncRedisSaver requires Redis Stack or RediSearch module")
            logger.error("   Please install Redis Stack: https://redis.io/docs/getting-started/install-stack/")
            await redis_client.aclose()
            return False
        
        logger.info("✅ RediSearch module found")
        
        # 创建 AsyncRedisSaver
        checkpointer = AsyncRedisSaver(redis_url)
        logger.info("✅ AsyncRedisSaver created successfully")
        
        # 测试索引（通过查询触发索引创建）
        logger.info("📝 Testing index initialization...")
        test_config = {
            "configurable": {
                "thread_id": "test-init-thread",
            }
        }
        
        # 尝试获取 checkpoint（如果索引不存在会自动创建）
        result = await checkpointer.aget_tuple(test_config)
        logger.info(f"✅ Index test successful (result: {result is not None})")
        
        await redis_client.aclose()
        logger.info("✅ Redis indexes initialized successfully!")
        logger.info("🎉 LangGraph AsyncRedisSaver is ready to use")
        
        return True
        
    except ImportError:
        logger.error("❌ langgraph-checkpoint-redis not installed")
        logger.error("   Install it with: pip install langgraph-checkpoint-redis")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis checkpointer: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("🚀 Starting Redis Checkpointer initialization...")
    logger.info(f"📊 Redis Host: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"📊 Redis DB: {settings.redis_db}")
    
    success = await init_redis_checkpointer()
    
    if success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Initialization completed successfully!")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("")
        logger.error("=" * 60)
        logger.error("❌ Initialization failed!")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

