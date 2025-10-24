"""
对话历史数据初始化脚本

创建一些模拟的对话历史数据，用于测试管理平台统计功能。
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4

from src.core.config import get_settings
from src.db.base import DatabaseService
from src.db.models import ConversationHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_conversations():
    """创建示例对话数据"""
    settings = get_settings()
    db_service = DatabaseService(settings.postgres_url)
    
    try:
        async with db_service.get_session() as session:
            # 创建多个会话
            sessions = []
            for i in range(10):
                session_id = str(uuid4())
                sessions.append(session_id)
            
            # 为每个会话创建多条对话记录
            conversations = []
            base_time = datetime.utcnow()
            
            for i, session_id in enumerate(sessions):
                # 每个会话有 2-5 条对话
                num_messages = random.randint(2, 5)
                
                for j in range(num_messages):
                    # 随机时间（最近7天内）
                    days_ago = random.randint(0, 7)
                    hours_ago = random.randint(0, 23)
                    minutes_ago = random.randint(0, 59)
                    
                    created_at = base_time - timedelta(
                        days=days_ago, 
                        hours=hours_ago, 
                        minutes=minutes_ago
                    )
                    
                    # 模拟用户消息
                    user_messages = [
                        "你好，我想了解一下你们的产品",
                        "你们的退货政策是什么？",
                        "iPhone 15 的价格是多少？",
                        "配送需要多长时间？",
                        "支持哪些支付方式？",
                        "保修期是多长？",
                        "有优惠活动吗？",
                        "如何联系客服？"
                    ]
                    
                    assistant_messages = [
                        "您好！很高兴为您服务。我们有多款优质产品，请问您对哪类产品感兴趣？",
                        "我们的退货政策是30天内可以无理由退货，商品需保持原包装。",
                        "iPhone 15 128GB 售价 ¥5,999，256GB 售价 ¥6,999。",
                        "一般情况下3-5个工作日送达，偏远地区可能需要7-10天。",
                        "我们支持微信支付、支付宝、银联卡等多种支付方式。",
                        "所有产品享有1年免费保修服务。",
                        "目前有新品上市优惠，详情请咨询客服。",
                        "您可以通过在线客服、电话或邮件联系我们。"
                    ]
                    
                    # 创建对话记录（用户消息和AI回复在一条记录中）
                    conversation = ConversationHistory(
                        session_id=session_id,
                        user_message=random.choice(user_messages),
                        ai_response=random.choice(assistant_messages),
                        confidence_score=random.uniform(0.7, 0.95),
                        created_at=created_at
                    )
                    conversations.append(conversation)
            
            # 批量插入
            session.add_all(conversations)
            await session.commit()
            
            logger.info(f"✅ 成功创建 {len(conversations)} 条对话记录")
            logger.info(f"📊 涉及 {len(sessions)} 个会话")
            
    except Exception as e:
        logger.error(f"❌ 创建对话数据失败: {e}")
        raise
    finally:
        await db_service.close()


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("📦 初始化对话历史数据")
    logger.info("=" * 50)
    
    await create_sample_conversations()
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ 对话数据初始化完成！")
    logger.info("=" * 50)
    logger.info("\n💡 现在可以查看管理平台统计:")
    logger.info("   http://localhost:5173/")


if __name__ == "__main__":
    asyncio.run(main())
