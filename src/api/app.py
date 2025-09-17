#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的FastAPI应用
支持启动时自动加载和状态监控
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from ..config.settings import settings
from .routes import router
from ..infrastructure.startup import get_startup_manager

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """创建增强的FastAPI应用"""
    
    app = FastAPI(
        title="法智导航 - 增强版",
        version="1.1.0",
        description="增强的法律检索系统，支持启动状态监控"
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 启动事件处理器
    @app.on_event("startup")
    async def startup_event():
        """应用启动时的处理"""
        logger.info("=== 法智导航系统启动 ===")
        logger.info("Starting background data loading...")
        
        try:
            # 获取启动管理器并开始后台加载
            startup_manager = get_startup_manager()
            
            # 添加状态观察者（可选，用于日志记录）
            def log_status_update(status):
                if status.current_step:
                    step = status.steps.get(status.current_step)
                    if step:
                        logger.info(f"Loading: {step.name} - {step.progress:.1f}%")
            
            startup_manager.add_observer(log_status_update)
            
            # 启动后台加载
            startup_manager.start_background_loading()
            
            logger.info("Background loading started successfully")
            logger.info("System will be ready shortly...")
            
        except Exception as e:
            logger.error(f"Failed to start background loading: {e}", exc_info=True)
    
    @app.on_event("shutdown") 
    async def shutdown_event():
        """应用关闭时的处理"""
        logger.info("=== 法智导航系统关闭 ===")
        logger.info("Cleaning up resources...")
        
        try:
            # 这里可以添加清理逻辑
            # 比如：清理缓存、关闭连接等
            pass
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    # 根路径 - 增强版状态信息
    @app.get("/")
    async def root():
        startup_manager = get_startup_manager()
        system_summary = startup_manager.get_summary()
        
        return {
            "message": "法智导航 - 增强版",
            "status": "ready" if startup_manager.is_ready() else "loading",
            "startup_info": {
                "is_loading": system_summary["is_loading"],
                "overall_progress": system_summary["overall_progress"],
                "current_step": system_summary["current_step"],
                "is_ready": system_summary["is_ready"]
            }
        }
    
    # 健康检查 - 增强版
    @app.get("/health")
    async def health():
        startup_manager = get_startup_manager()
        return {
            "status": "healthy" if startup_manager.is_ready() else "loading",
            "ready": startup_manager.is_ready(),
            "loading": startup_manager.is_loading(),
            "startup_summary": startup_manager.get_summary()
        }
    
    # 添加API路由
    app.include_router(router, prefix="/api")
    
    # 静态文件服务 - 前端
    try:
        frontend_path = Path(__file__).parent.parent.parent / "frontend"
        if frontend_path.exists():
            app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
            logger.info(f"Frontend mounted at /ui from {frontend_path}")
    except Exception as e:
        logger.error(f"Failed to mount frontend: {e}")
    
    return app