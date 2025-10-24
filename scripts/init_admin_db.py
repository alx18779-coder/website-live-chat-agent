#!/usr/bin/env python3
"""
初始化管理平台数据库

该脚本用于：
1. 创建数据库表结构
2. 创建默认管理员账户
3. 验证数据库连接
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.core.config import get_settings
from src.db.base import DatabaseService, Base
from src.db.models import AdminUser
from src.core.admin_security_bcrypt import AdminSecurity


async def init_database():
    """初始化数据库"""
    print("🚀 开始初始化管理平台数据库...")
    
    try:
        # 获取配置
        settings = get_settings()
        print(f"📊 数据库配置: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        
        # 创建数据库服务
        db_service = DatabaseService(settings.postgres_url)
        print("✅ 数据库连接已建立")
        
        # 创建所有表
        print("📋 创建数据库表...")
        async with db_service.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ 数据库表创建完成")
        
        # 创建默认管理员账户
        print("👤 创建默认管理员账户...")
        security = AdminSecurity(settings.jwt_secret_key, settings.jwt_expire_minutes)
        
        # 限制密码长度（bcrypt 限制 72 字节）
        password = settings.admin_password[:72] if len(settings.admin_password) > 72 else settings.admin_password
        hashed_password = security.get_password_hash(password)
        
        # 检查是否已存在管理员账户
        async with db_service.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == settings.admin_username)
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # 创建管理员账户
                admin_user = AdminUser(
                    username=settings.admin_username,
                    password_hash=hashed_password,
                    is_active="Y"
                )
                
                session.add(admin_user)
                await session.commit()
                
                print(f"✅ 默认管理员账户创建成功: {settings.admin_username}")
            else:
                print(f"ℹ️  管理员账户已存在: {settings.admin_username}")
        
        print(f"   用户名: {settings.admin_username}")
        print(f"   密码哈希: {hashed_password[:20]}...")
        print("✅ 管理员账户配置完成")
        
        # 验证连接
        print("🔍 验证数据库连接...")
        async with db_service.get_session() as session:
            # 执行简单查询验证连接
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ 数据库连接验证成功")
        
        print("\n🎉 数据库初始化完成！")
        print("\n📝 下一步操作：")
        print("1. 启动服务: docker-compose up -d")
        print("2. 访问管理平台: http://localhost:3000")
        print(f"3. 使用账户登录: {settings.admin_username} / {settings.admin_password}")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        if 'db_service' in locals():
            await db_service.engine.dispose()


async def check_database_connection():
    """检查数据库连接"""
    print("🔍 检查数据库连接...")
    
    try:
        settings = get_settings()
        db_service = DatabaseService(settings.postgres_url)
        
        # 使用 async_session 直接创建会话
        async with db_service.get_session() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接正常，版本: {version}")
            return True
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    finally:
        if 'db_service' in locals():
            await db_service.engine.dispose()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="管理平台数据库初始化工具")
    parser.add_argument("--check-only", action="store_true", help="仅检查数据库连接")
    args = parser.parse_args()
    
    if args.check_only:
        success = await check_database_connection()
        sys.exit(0 if success else 1)
    else:
        await init_database()


if __name__ == "__main__":
    asyncio.run(main())