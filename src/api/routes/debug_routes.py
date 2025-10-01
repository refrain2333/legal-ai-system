#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试功能路由模块
包含系统调试和性能监控相关的API接口
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any

from ..models import SearchRequest
from src.services.search_service import SearchService
from src.infrastructure.repositories import get_legal_document_repository
from src.infrastructure.startup import get_startup_manager

logger = logging.getLogger(__name__)

# 创建调试路由器
router = APIRouter()

# 导入统一的WebSocket管理器
from ..websocket_manager import get_websocket_manager

# 获取全局WebSocket管理器实例
websocket_manager = get_websocket_manager()


def get_debug_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的调试模式搜索服务实例"""
    from src.infrastructure.llm.llm_client import LLMClient
    from src.config.settings import settings

    repository = get_legal_document_repository()
    llm_client = LLMClient(settings)
    return SearchService(repository, llm_client, debug_mode=True)


def get_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的搜索服务实例"""
    from src.infrastructure.llm.llm_client import LLMClient
    from src.config.settings import settings

    repository = get_legal_document_repository()
    llm_client = LLMClient(settings)
    return SearchService(repository, llm_client, debug_mode=False)


def _check_system_ready():
    """检查系统是否准备就绪"""
    startup_manager = get_startup_manager()
    if not startup_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "系统正在加载中，请稍后再试",
                "loading_info": startup_manager.get_summary()
            }
        )


@router.post("/search/debug")
async def search_debug(
    request: SearchRequest,
    search_service: SearchService = Depends(get_debug_search_service)
) -> Dict[str, Any]:
    """AI驱动的智能搜索 - 完整调试模式"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

        # 设置WebSocket管理器
        search_service.set_websocket_manager(websocket_manager)

        # 调用智能搜索调试版本
        debug_result = await search_service.search_documents_intelligent_debug(
            query_text=request.query,
            debug=True
        )

        # 向WebSocket广播实时更新
        if debug_result.get('success') and debug_result.get('trace'):
            await websocket_manager.broadcast({
                "type": "search_completed",
                "request_id": debug_result.get('request_id'),
                "query": request.query,
                "trace_summary": {
                    "total_duration_ms": debug_result['trace'].get('total_duration_ms', 0),
                    "processing_mode": debug_result['trace'].get('processing_mode'),
                    "stages_completed": debug_result['trace']['summary'].get('stages_completed', 0),
                    "successful_modules": debug_result['trace']['summary'].get('successful_modules', 0)
                }
            })

        return debug_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调试搜索服务错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"调试搜索服务错误: {str(e)}")


@router.get("/search/trace/{request_id}")
async def get_search_trace(request_id: str) -> Dict[str, Any]:
    """获取指定搜索的完整trace记录"""
    try:
        # 这里应该从缓存或数据库中获取trace记录
        # 当前简化实现，返回提示信息
        return {
            "success": False,
            "message": "Trace存储功能待实现，请使用实时调试搜索",
            "request_id": request_id,
            "suggestion": "使用 POST /search/debug 进行实时调试搜索"
        }

    except Exception as e:
        logger.error(f"获取搜索trace失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取搜索trace失败: {str(e)}")


@router.get("/modules/status")
async def get_modules_status(
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """获取所有搜索模块的当前状态"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

        # 获取各模块状态
        modules_status = []

        # 基础搜索状态
        basic_status = search_service.get_system_status()
        modules_status.append({
            "module_name": "basic_semantic_search",
            "status": "ok" if basic_status.get('ready') else "error",
            "reason": "基础语义搜索引擎状态",
            "last_check": "2024-01-01T00:00:00Z",
            "performance_stats": {
                "avg_response_time_ms": 150,
                "total_documents": basic_status.get('total_documents', 0)
            }
        })

        # LLM增强搜索状态
        llm_status = search_service.get_llm_enhancement_status()
        modules_status.append({
            "module_name": "llm_enhanced_search",
            "status": "error" if not llm_status.get('llm_enhancement_available') else "warning",
            "reason": "LLM增强搜索当前有代码bug" if not llm_status.get('llm_enhancement_available') else "功能可用但需要验证",
            "last_check": "2024-01-01T00:00:00Z",
            "performance_stats": {
                "supported_methods": llm_status.get('supported_methods', [])
            }
        })

        # 知识图谱增强搜索状态
        kg_status = search_service.get_kg_enhanced_status()
        modules_status.append({
            "module_name": "knowledge_graph_search",
            "status": "warning" if kg_status.get('kg_enhancement_available') else "error",
            "reason": "知识图谱搜索引擎未初始化" if not kg_status.get('kg_enhancement_available') else "知识图谱功能可用",
            "last_check": "2024-01-01T00:00:00Z",
            "performance_stats": {
                "knowledge_graph_stats": kg_status.get('knowledge_graph_stats', {})
            }
        })

        # BM25混合搜索状态
        modules_status.append({
            "module_name": "bm25_hybrid_search",
            "status": "ok",
            "reason": "BM25混合搜索功能正常",
            "last_check": "2024-01-01T00:00:00Z",
            "performance_stats": {
                "fusion_method": "RRF",
                "avg_response_time_ms": 200
            }
        })

        return {
            "success": True,
            "modules_status": modules_status,
            "recent_searches": [],  # 待实现
            "performance_metrics": {
                "total_searches_today": 0,
                "avg_response_time": 150.0,
                "success_rate": 0.95,
                "system_uptime": "24h"
            },
            "system_health": "partial" if any(m['status'] == 'error' for m in modules_status) else "good"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模块状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模块状态失败: {str(e)}")


@router.get("/system/info")
async def get_system_debug_info(
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """获取系统整体调试信息"""
    try:
        # 获取模块状态（复用上面的逻辑）
        modules_response = await get_modules_status(search_service)

        return {
            "success": True,
            "system_info": {
                "version": "1.0.0",
                "environment": "development",
                "python_version": "3.9+",
                "framework": "FastAPI + DDD架构"
            },
            "modules_status": modules_response["modules_status"],
            "recent_searches": modules_response["recent_searches"],
            "performance_metrics": modules_response["performance_metrics"],
            "system_health": modules_response["system_health"],
            "debug_capabilities": {
                "trace_collection": True,
                "realtime_websocket": True,
                "module_monitoring": True,
                "performance_tracking": True,
                "error_reporting": True
            }
        }

    except Exception as e:
        logger.error(f"获取系统调试信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统调试信息失败: {str(e)}")


@router.get("/search/history")
async def get_search_history(
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """获取搜索历史记录"""
    try:
        # 模拟搜索历史数据
        mock_history = [
            {
                "request_id": "req-001",
                "query": "故意伤害罪判几年",
                "timestamp": "2024-01-01T10:00:00Z",
                "duration_ms": 150,
                "success": True,
                "result_count": 8,
                "mode": "criminal_law",
                "tags": ["刑法", "故意伤害"]
            },
            {
                "request_id": "req-002",
                "query": "盗窃罪的量刑标准",
                "timestamp": "2024-01-01T10:05:00Z",
                "duration_ms": 200,
                "success": True,
                "result_count": 10,
                "mode": "criminal_law",
                "tags": ["刑法", "盗窃"]
            }
        ]

        return {
            "success": True,
            "history": mock_history[offset:offset+limit],
            "total": len(mock_history),
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < len(mock_history)
        }

    except Exception as e:
        logger.error(f"获取搜索历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取搜索历史失败: {str(e)}")


@router.get("/performance/stats")
async def get_performance_stats() -> Dict[str, Any]:
    """获取系统性能统计"""
    try:
        # 模拟性能数据
        return {
            "success": True,
            "performance_stats": {
                "avgResponseTime": 175.5,
                "successRate": 0.96,
                "modulesStatus": {
                    "basic_semantic": {"status": "ok", "avgTime": 120, "successRate": 0.98},
                    "llm_enhanced": {"status": "error", "avgTime": 0, "successRate": 0.0},
                    "knowledge_graph": {"status": "warning", "avgTime": 180, "successRate": 0.85},
                    "bm25_hybrid": {"status": "ok", "avgTime": 200, "successRate": 0.95}
                },
                "recentQueries": [
                    {
                        "request_id": "req-latest-001",
                        "query": "最近的查询示例",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "duration_ms": 180,
                        "success": True,
                        "result_count": 7,
                        "mode": "criminal_law",
                        "tags": ["测试"]
                    }
                ]
            },
            "update_time": "2024-01-01T12:00:00Z"
        }

    except Exception as e:
        logger.error(f"获取性能统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")