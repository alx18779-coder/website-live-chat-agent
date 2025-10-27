"""
数据库依赖注入

提供全局 DatabaseService 实例的依赖注入函数。
"""

from fastapi import Request

from src.db.base import DatabaseService


def get_db_service(request: Request) -> DatabaseService:
    """
    获取全局 DatabaseService 实例

    Args:
        request: FastAPI Request 对象

    Returns:
        DatabaseService: 全局单例 DatabaseService 实例

    Raises:
        RuntimeError: 如果 DatabaseService 未初始化

    Note:
        DatabaseService 在应用启动时（src.main:lifespan）初始化，
        并在应用关闭时释放。这样可以避免连接池泄漏问题。
    """
    if not hasattr(request.app.state, 'db_service'):
        raise RuntimeError(
            "Global DatabaseService not initialized. "
            "This should be set up in the app lifespan (src.main:lifespan)."
        )
    return request.app.state.db_service

