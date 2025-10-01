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
from .error_handlers import (
    legal_search_exception_handler,
    system_not_ready_exception_handler,
    llm_service_exception_handler,
    knowledge_graph_exception_handler,
    vector_search_exception_handler,
    validation_exception_handler
)
from ..domains.exceptions import (
    LegalSearchException,
    SystemNotReadyException,
    LLMServiceException,
    KnowledgeGraphException,
    VectorSearchException,
    ValidationException
)

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """创建增强的FastAPI应用"""
    
    app = FastAPI(
        title="法智导航 - 增强版",
        version="1.1.0",
        description="增强的法律检索系统，支持启动状态监控"
    )
    
    # CORS中间件 - 支持WebSocket
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS + ["*"],  # WebSocket需要更宽松的CORS
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册分层异常处理器
    app.add_exception_handler(LegalSearchException, legal_search_exception_handler)
    app.add_exception_handler(SystemNotReadyException, system_not_ready_exception_handler)
    app.add_exception_handler(LLMServiceException, llm_service_exception_handler)
    app.add_exception_handler(KnowledgeGraphException, knowledge_graph_exception_handler)
    app.add_exception_handler(VectorSearchException, vector_search_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    
    # 启动事件处理器
    @app.on_event("startup")
    async def startup_event():
        """应用启动时的处理"""
        logger.info("=== 法智导航系统启动 ===")
        logger.info("Starting background data loading...")
        
        try:
            # 获取启动管理器（会自动开始后台加载）
            startup_manager = get_startup_manager()
            
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
    
    # 添加API路由（包括WebSocket）
    app.include_router(router, prefix="/api")
    
    # 静态文件服务 - 前端
    try:
        frontend_path = Path(__file__).parent.parent.parent / "frontend"
        if frontend_path.exists():
            app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
            logger.info(f"Frontend mounted at /ui from {frontend_path}")

            # 添加根路径重定向到前端首页
            @app.get("/frontend")
            async def redirect_to_frontend():
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="/ui/index.html")

    except Exception as e:
        logger.error(f"Failed to mount frontend: {e}")
    
    return app