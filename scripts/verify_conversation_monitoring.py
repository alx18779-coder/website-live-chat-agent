"""
验证对话监控功能是否正常工作

这个脚本会：
1. 检查 PostgreSQL 连接
2. 检查对话表是否存在
3. 查询最近的对话记录
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.core.config import get_settings
from src.db.base import DatabaseService
from src.db.repositories.conversation_repository import ConversationRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def verify_conversation_monitoring():
    """验证对话监控功能"""
    settings = get_settings()
    
    logger.info("🚀 开始验证对话监控功能...")
    logger.info(f"📊 PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    
    try:
        # 1. 测试数据库连接
        logger.info("📝 测试数据库连接...")
        db_service = DatabaseService(settings.postgres_url)
        
        async with db_service.get_session() as session:
            # 测试连接
            result = await session.execute("SELECT 1")
            logger.info("✅ PostgreSQL 连接成功")
            
            # 2. 检查对话表是否存在
            logger.info("📝 检查对话表...")
            result = await session.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'conversations'
                )
            """)
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("✅ conversations 表存在")
            else:
                logger.error("❌ conversations 表不存在！")
                logger.error("   请运行: alembic upgrade head")
                return False
            
            # 3. 查询对话记录
            logger.info("📝 查询最近的对话记录...")
            repo = ConversationRepository(session)
            
            conversations = await repo.get_conversations(skip=0, limit=5)
            total = await repo.count_conversations()
            
            logger.info(f"✅ 对话记录总数: {total}")
            
            if conversations:
                logger.info(f"📊 最近 {len(conversations)} 条对话:")
                for conv in conversations:
                    logger.info(
                        f"  - ID: {conv.id[:8]}... | "
                        f"Session: {conv.session_id[:8]}... | "
                        f"创建时间: {conv.created_at}"
                    )
            else:
                logger.warning("⚠️  数据库中没有对话记录")
                logger.warning("   这可能是因为：")
                logger.warning("   1. 还没有对话请求")
                logger.warning("   2. 对话保存失败（检查应用日志）")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ 对话监控功能验证完成！")
            logger.info("=" * 60)
            logger.info("")
            logger.info("📌 访问对话监控 API:")
            logger.info("   1. 先登录获取 token:")
            logger.info(f"      curl -X POST 'http://localhost:8000/api/admin/auth/login' \\")
            logger.info(f"        -H 'Content-Type: application/json' \\")
            logger.info(f"        -d '{{\"username\": \"admin\", \"password\": \"your_password\"}}'")
            logger.info("")
            logger.info("   2. 使用 token 查询对话历史:")
            logger.info(f"      curl -H 'Authorization: Bearer <token>' \\")
            logger.info(f"        'http://localhost:8000/api/admin/conversations/history'")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await verify_conversation_monitoring()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

