#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由注册中心
统一管理所有路由模块
"""

from fastapi import APIRouter
from .search_routes import router as search_router
from .debug_routes import router as debug_router
from .knowledge_graph_routes import router as kg_router
from .system_routes import router as system_router
from .websocket_routes import router as ws_router


def create_api_router() -> APIRouter:
    """
    创建统一的API路由器

    Returns:
        配置好的API路由器
    """
    api_router = APIRouter()

    # 注册各功能模块路由
    api_router.include_router(search_router, tags=["search"])
    api_router.include_router(debug_router, tags=["debug"])
    api_router.include_router(kg_router, prefix="/knowledge_graph", tags=["knowledge_graph"])
    api_router.include_router(system_router, tags=["system"])
    api_router.include_router(ws_router, tags=["websocket"])

    return api_router


# 为了向后兼容，暂时保留原有的导入方式
# 后续可以逐步迁移到新的路由结构
router = create_api_router()

__all__ = ["create_api_router", "router"]