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
        
        # 显式创建索引（如果有 setup 方法）
        logger.info("📝 Setting up indexes...")
        if hasattr(checkpointer, 'setup'):
            await checkpointer.setup()
            logger.info("✅ Indexes setup completed")
        else:
            logger.info("ℹ️  No explicit setup method found, indexes will be created on first use")
        
        # 测试索引（通过实际的 checkpoint 写入触发所有索引创建）
        logger.info("📝 Initializing indexes through test checkpoint write...")
        
        from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
        
        test_config = {
            "configurable": {
                "thread_id": "init-test-thread",
                "checkpoint_ns": "",
                "checkpoint_id": "init-test-checkpoint"
            }
        }
        
        # 创建一个最小化的测试 checkpoint
        test_checkpoint = Checkpoint(
            v=1,
            id="init-test-checkpoint",
            ts="2024-01-01T00:00:00.000000+00:00",
            channel_values={"__start__": "test"},
            channel_versions={"__start__": 1},
            versions_seen={"__start__": {"__start__": 1}},
            pending_sends=[]
        )
        
        test_metadata = CheckpointMetadata(
            source="input",
            step=0,
            writes={"__start__": "test"},
            parents={}
        )
        
        # 执行写入操作（这会触发所有索引的创建，包括 checkpoint_writes）
        logger.info("📝 Writing test checkpoint to trigger index creation...")
        await checkpointer.aput(
            test_config,
            test_checkpoint,
            test_metadata,
            {}
        )
        logger.info("✅ Test checkpoint written successfully")
        
        # 验证读取
        logger.info("📝 Verifying checkpoint read...")
        result = await checkpointer.aget_tuple(test_config)
        if result:
            logger.info("✅ Checkpoint read verification successful")
        else:
            logger.warning("⚠️ Checkpoint read returned None (this is OK for initialization)")
        
        await redis_client.aclose()
        logger.info("✅ All Redis indexes initialized successfully!")
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

