"""
法智导航 - 智能法律匹配与咨询系统
Legal Navigation AI - Intelligent Legal Matching and Consultation System

主入口文件
"""

import asyncio
import sys
import uvicorn
from pathlib import Path

from .config.settings import settings
from .api.app import create_app
from .utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)


async def startup():
    """应用启动初始化"""
    logger.info("🚀 启动法智导航系统...")
    logger.info(f"📍 环境: {settings.APP_ENV}")
    logger.info(f"🔧 调试模式: {settings.DEBUG}")
    logger.info(f"🌐 服务地址: http://{settings.HOST}:{settings.PORT}")


def main():
    """主函数"""
    try:
        # 创建FastAPI应用
        app = create_app()
        
        # 添加启动事件
        @app.on_event("startup")
        async def on_startup():
            await startup()
        
        # 启动服务器
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            workers=1 if settings.DEBUG else settings.WORKERS,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()