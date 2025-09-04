"""
日志配置和管理模块
"""

import sys
import logging
from pathlib import Path
from loguru import logger
from typing import Union

from src.config.settings import settings


class InterceptHandler(logging.Handler):
    """将标准logging重定向到loguru"""
    
    def emit(self, record):
        # 获取对应的Loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用者的frame
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger(name: Union[str, None] = None):
    """
    设置日志系统
    
    Args:
        name: 日志器名称
        
    Returns:
        logger: 配置好的日志器实例
    """
    
    # 创建日志目录
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 移除默认的loguru handler
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        colorize=True,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )
    
    # 添加文件输出
    logger.add(
        settings.LOG_FILE,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=settings.LOG_LEVEL,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        compression="zip",
        encoding="utf-8"
    )
    
    # 拦截标准logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 为特定库设置日志级别
    for _log in ['uvicorn', 'uvicorn.error', 'uvicorn.access']:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
    
    return logger