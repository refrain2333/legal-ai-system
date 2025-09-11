#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的FastAPI应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config.settings import settings
from .routes import router

def create_app() -> FastAPI:
    """创建简化的FastAPI应用"""
    
    app = FastAPI(
        title="法智导航 - 简化版",
        version="1.0.0",
        description="简化的法律检索系统"
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 根路径
    @app.get("/")
    async def root():
        return {"message": "法智导航 - 简化版", "status": "running"}
    
    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    # 添加API路由
    app.include_router(router, prefix="/api")
    
    # 静态文件服务 - 前端
    try:
        frontend_path = Path(__file__).parent.parent.parent / "frontend"
        if frontend_path.exists():
            app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
            print(f"Frontend mounted at /ui from {frontend_path}")
    except Exception as e:
        print(f"Failed to mount frontend: {e}")
    
    return app