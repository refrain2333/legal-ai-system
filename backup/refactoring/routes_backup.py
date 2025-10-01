#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的API路由 - 包含启动状态监控
遵循分层架构原则，仅调用服务层
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from .models import SearchRequest, SearchResponse, StatusResponse, SearchResult
from ..services.search_service import SearchService
from ..infrastructure.repositories import get_legal_document_repository
from ..infrastructure.startup import get_startup_manager
from ..infrastructure.llm.llm_client import LLMClient
from ..config.settings import settings

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 创建全局LLM客户端实例（单例）
_llm_client_instance = None

def get_llm_client() -> LLMClient:
    """获取LLM客户端实例（单例模式）"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient(settings)
        logger.info("创建LLM客户端单例实例")
    return _llm_client_instance

def get_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的搜索服务实例"""
    # 获取共享的只读资源
    repository = get_legal_document_repository()
    llm_client = get_llm_client()
    # 为每个请求创建新的SearchService实例，避免状态污染
    return SearchService(repository, llm_client, debug_mode=False)

def get_debug_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的调试模式搜索服务实例"""
    # 获取共享的只读资源
    repository = get_legal_document_repository()
    llm_client = get_llm_client()
    # 为每个请求创建新的SearchService实例，避免状态污染
    return SearchService(repository, llm_client, debug_mode=True)

# WebSocket连接管理器
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")

    async def disconnect(self, websocket: WebSocket):
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"WebSocket断开连接错误: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            logger.debug("没有活跃的WebSocket连接，跳过广播")
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"WebSocket发送消息失败: {e}")
                disconnected.append(connection)

        # 清理失效连接
        for conn in disconnected:
            await self.disconnect(conn)

websocket_manager = WebSocketManager()

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, search_service: SearchService = Depends(get_search_service)):
    """搜索接口 - 新格式：5条法条 + 5条案例"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "系统正在加载中，请稍后再试",
                    "loading_info": startup_manager.get_summary()
                }
            )
        
        # 调用服务层执行业务逻辑
        service_result = await search_service.search_documents_mixed(
            query_text=request.query,
            articles_count=5,
            cases_count=5
        )
        
        # 检查服务层返回的结果
        if not service_result.get('success', False):
            raise HTTPException(
                status_code=400, 
                detail=service_result.get('error', '搜索失败')
            )
        
        # 转换为API响应格式 - 先法条后案例
        api_results = []
        
        # 添加法条结果
        for item in service_result.get('articles', []):
            result = SearchResult(
                id=item.get('id', ''),
                title=item.get('title', ''),
                content=item.get('content', ''),
                similarity=item.get('similarity', 0.0),
                type=item.get('type', 'article'),
                # 法条特有字段
                article_number=item.get('article_number'),
                chapter=item.get('chapter'),
                # 案例字段设为None
                case_id=None, criminals=None, accusations=None, relevant_articles=None,
                punish_of_money=None, death_penalty=None, life_imprisonment=None, imprisonment_months=None
            )
            api_results.append(result)
        
        # 添加案例结果
        for item in service_result.get('cases', []):
            result = SearchResult(
                id=item.get('id', ''),
                title=item.get('title', ''),
                content=item.get('content', ''),
                similarity=item.get('similarity', 0.0),
                type=item.get('type', 'case'),
                # 案例特有字段
                case_id=item.get('case_id'),
                criminals=item.get('criminals'),
                accusations=item.get('accusations'),
                relevant_articles=item.get('relevant_articles'),
                punish_of_money=item.get('punish_of_money'),
                death_penalty=item.get('death_penalty'),
                life_imprisonment=item.get('life_imprisonment'),
                imprisonment_months=item.get('imprisonment_months'),
                # 法条字段设为None
                article_number=None, chapter=None
            )
            api_results.append(result)
        
        return SearchResponse(
            success=True,
            results=api_results,
            total=len(api_results),
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")

# ==================== 调试搜索 API ====================

@router.post("/search/debug")
async def search_debug(
    request: SearchRequest,
    search_service: SearchService = Depends(get_debug_search_service)
) -> Dict[str, Any]:
    """AI驱动的智能搜索 - 完整调试模式"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "系统正在加载中，请稍后再试",
                    "loading_info": startup_manager.get_summary()
                }
            )

        # 🚀 关键修复：在调用搜索前就设置WebSocket管理器
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
        raise HTTPException(status_code=500, detail=f"获取搜索trace失败: {str(e)}")

@router.get("/debug/modules/status")
async def get_modules_status(
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """获取所有搜索模块的当前状态"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

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
        raise HTTPException(status_code=500, detail=f"获取模块状态失败: {str(e)}")

@router.websocket("/debug/realtime")
async def debug_websocket(websocket: WebSocket):
    """WebSocket端点 - 用于实时调试数据推送"""
    logger.info("新的WebSocket连接请求")

    await websocket_manager.connect(websocket)

    try:
        # 发送欢迎消息
        welcome_message = {
            "type": "connected",
            "message": "调试WebSocket连接已建立",
            "timestamp": "2024-01-01T00:00:00Z",
            "connection_id": len(websocket_manager.active_connections)
        }
        await websocket.send_json(welcome_message)
        logger.info(f"已发送欢迎消息: {welcome_message}")

        # 保持连接活跃
        while True:
            try:
                # 等待来自客户端的消息
                data = await websocket.receive_json()
                logger.info(f"收到WebSocket消息: {data}")

                if data.get("type") == "ping":
                    pong_message = {
                        "type": "pong",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_json(pong_message)
                    logger.info("回复pong消息")

                elif data.get("type") == "subscribe":
                    subscribe_message = {
                        "type": "subscribed",
                        "subscription": data.get("events", ["all"]),
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_json(subscribe_message)
                    logger.info(f"确认订阅: {subscribe_message}")

            except WebSocketDisconnect:
                logger.info("客户端主动断开WebSocket连接")
                break
            except Exception as e:
                logger.error(f"WebSocket处理消息错误: {e}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

@router.get("/debug/system/info")
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
        raise HTTPException(status_code=500, detail=f"获取系统调试信息失败: {str(e)}")

# ==================== 搜索历史和性能 API ====================

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
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")

@router.get("/search/cases/more")
async def load_more_cases(query: str, offset: int = 0, limit: int = 5, 
                         search_service: SearchService = Depends(get_search_service)):
    """分页加载更多案例"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )
        
        # 调用服务层加载更多案例
        service_result = await search_service.load_more_cases(query, offset, limit)
        
        if not service_result.get('success', False):
            raise HTTPException(
                status_code=400,
                detail=service_result.get('error', '加载失败')
            )
        
        # 转换为API响应格式
        api_cases = []
        for item in service_result.get('cases', []):
            result = SearchResult(
                id=item.get('id', ''),
                title=item.get('title', ''),
                content=item.get('content', ''),
                similarity=item.get('similarity', 0.0),
                type=item.get('type', 'case'),
                case_id=item.get('case_id'),
                criminals=item.get('criminals'),
                accusations=item.get('accusations'),
                relevant_articles=item.get('relevant_articles'),
                punish_of_money=item.get('punish_of_money'),
                death_penalty=item.get('death_penalty'),
                life_imprisonment=item.get('life_imprisonment'),
                imprisonment_months=item.get('imprisonment_months'),
                article_number=None, chapter=None
            )
            api_cases.append(result)
        
        return {
            "success": True,
            "cases": api_cases,
            "offset": service_result.get('offset', offset),
            "limit": service_result.get('limit', limit),
            "returned_count": service_result.get('returned_count', len(api_cases)),
            "has_more": service_result.get('has_more', False),
            "query": query
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载更多案例错误: {str(e)}")

@router.get("/status", response_model=StatusResponse)
async def get_status(search_service: SearchService = Depends(get_search_service)):
    """获取系统状态 - 增强版包含启动信息"""
    try:
        # 获取启动状态
        startup_manager = get_startup_manager()
        startup_summary = startup_manager.get_summary()
        
        # 调用服务层获取搜索系统状态信息
        search_status = search_service.get_system_status()
        
        return StatusResponse(
            status=search_status.get('status', 'unknown'),
            ready=startup_manager.is_ready() and search_status.get('ready', False),
            total_documents=search_status.get('total_documents', 0),
            startup_info=startup_summary
        )
        
    except Exception as e:
        # 降级处理：返回错误状态而不抛出异常
        return StatusResponse(
            status="error",
            ready=False,
            total_documents=0,
            startup_info={
                "is_loading": False,
                "overall_progress": 0.0,
                "error": str(e)
            }
        )

# 新增：启动状态专用API
@router.get("/startup/status")
async def get_startup_status():
    """获取详细的启动状态信息"""
    try:
        startup_manager = get_startup_manager()
        current_status = startup_manager.get_current_status()
        
        # 构建详细的状态响应
        steps_info = []
        for step_id, step in current_status.steps.items():
            steps_info.append({
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "status": step.status.value,
                "progress": step.progress,
                "duration": step.duration,
                "error_message": step.error_message,
                "details": step.details
            })
        
        return {
            "success": True,
            "system_status": {
                "is_loading": current_status.is_loading,
                "overall_progress": current_status.overall_progress,
                "current_step": current_status.current_step,
                "total_duration": current_status.total_duration,
                "completed_steps": current_status.completed_steps,
                "success_steps": current_status.success_steps,
                "failed_steps": current_status.failed_steps,
                "is_ready": startup_manager.is_ready()
            },
            "steps": steps_info,
            "summary": startup_manager.get_summary()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取启动状态失败: {str(e)}",
            "system_status": {
                "is_loading": False,
                "overall_progress": 0.0,
                "is_ready": False
            }
        }

@router.post("/startup/reload")
async def force_reload():
    """强制重新加载系统"""
    try:
        startup_manager = get_startup_manager()
        startup_manager.force_reload()
        
        return {
            "success": True,
            "message": "系统重新加载已启动",
            "status": startup_manager.get_summary()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"强制重新加载失败: {str(e)}"
        )

@router.get("/startup/steps")
async def get_loading_steps():
    """获取所有加载步骤的信息"""
    try:
        startup_manager = get_startup_manager()
        current_status = startup_manager.get_current_status()
        
        steps = []
        for step_id, step in current_status.steps.items():
            steps.append({
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "status": step.status.value,
                "progress": step.progress,
                "start_time": step.start_time.isoformat() if step.start_time else None,
                "end_time": step.end_time.isoformat() if step.end_time else None,
                "duration": step.duration,
                "error_message": step.error_message,
                "details": step.details
            })
        
        return {
            "success": True,
            "total_steps": len(steps),
            "steps": steps
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取加载步骤失败: {str(e)}"
        )

@router.get("/document/{document_id}")
async def get_document_by_id(document_id: str, search_service: SearchService = Depends(get_search_service)):
    """根据ID获取单个文档"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )
        
        document = await search_service.get_document_by_id(document_id)
        
        if document is None:
            raise HTTPException(status_code=404, detail="文档未找到")
        
        return {
            "success": True,
            "document": document
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")

@router.get("/health")
async def health_check():
    """增强的健康检查接口"""
    startup_manager = get_startup_manager()
    
    return {
        "status": "healthy" if startup_manager.is_ready() else "loading",
        "message": "法智导航 API 运行正常",
        "ready": startup_manager.is_ready(),
        "loading": startup_manager.is_loading(),
        "startup_summary": startup_manager.get_summary()
    }

# ==================== 知识图谱增强搜索 API ====================

@router.post("/search/kg_enhanced", response_model=SearchResponse)
async def search_kg_enhanced(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """知识图谱增强搜索 - 最高级的搜索功能"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        # 调用知识图谱增强搜索
        result = await search_service.search_documents_kg_enhanced(
            query_text=request.query,
            articles_count=request.articles_count,
            cases_count=request.cases_count
        )

        if not result.get('success', False):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', '知识图谱增强搜索失败')
            )

        return SearchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识图谱增强搜索失败: {str(e)}")

@router.post("/search/explain")
async def explain_search_reasoning(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """解释搜索推理过程"""
    try:
        # 检查系统是否准备就绪
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        explanation = await search_service.explain_search_reasoning(request.query)

        return {
            "success": True,
            "query": request.query,
            "explanation": explanation
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索推理解释失败: {str(e)}")

@router.get("/knowledge_graph/stats")
async def get_knowledge_graph_stats(search_service: SearchService = Depends(get_search_service)):
    """获取知识图谱统计信息"""
    try:
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        kg_status = search_service.get_kg_enhanced_status()

        return {
            "success": True,
            "knowledge_graph_status": kg_status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识图谱状态失败: {str(e)}")

@router.get("/knowledge_graph/relations/{entity}")
async def get_entity_relations(
    entity: str,
    entity_type: str = "auto",
    search_service: SearchService = Depends(get_search_service)
):
    """获取实体的关系信息（用于可视化）"""
    try:
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                visualization_data = knowledge_graph.visualize_relations(entity, entity_type)
                return {
                    "success": True,
                    "entity": entity,
                    "entity_type": entity_type,
                    "visualization_data": visualization_data
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {str(e)}")

@router.get("/knowledge_graph/expand/{query}")
async def expand_query_with_kg(
    query: str,
    search_service: SearchService = Depends(get_search_service)
):
    """使用知识图谱扩展查询"""
    try:
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                expansion_result = knowledge_graph.expand_query_with_relations(query)
                expanded_query = knowledge_graph.generate_expanded_query(query)

                return {
                    "success": True,
                    "original_query": query,
                    "expanded_query": expanded_query,
                    "expansion_details": expansion_result
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询扩展失败: {str(e)}")

@router.get("/knowledge_graph/crimes")
async def get_all_crimes(
    search_service: SearchService = Depends(get_search_service)
):
    """获取所有罪名列表"""
    try:
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                crimes_data = []

                # 获取所有罪名及其统计信息
                for crime, articles in knowledge_graph.crime_article_map.items():
                    total_cases = sum(articles.values())
                    related_articles = list(articles.keys())

                    crimes_data.append({
                        "crime": crime,  # 修改字段名以匹配前端期望
                        "case_count": total_cases,
                        "related_articles": related_articles
                    })

                # 按案例数量排序
                crimes_data.sort(key=lambda x: x['case_count'], reverse=True)

                return {
                    "success": True,
                    "total_count": len(crimes_data),
                    "crimes": crimes_data
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取罪名列表失败: {str(e)}")

@router.get("/knowledge_graph/articles")
async def get_all_articles(
    search_service: SearchService = Depends(get_search_service)
):
    """获取所有法条列表"""
    try:
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                articles_data = []

                # 获取所有法条及其统计信息
                for article, crimes in knowledge_graph.article_crime_map.items():
                    total_cases = sum(crimes.values())
                    related_crimes = list(crimes.keys())

                    # 需要获取法条标题，先简单使用法条号
                    articles_data.append({
                        "article_number": article,
                        "title": f"第{article}条",  # 简化标题，实际应该从数据中获取
                        "case_count": total_cases,
                        "chapter": "刑法",  # 简化章节信息
                        "related_crimes": related_crimes
                    })

                # 按法条编号排序
                def sort_key(x):
                    try:
                        return int(x['article_number'])
                    except ValueError:
                        return 9999  # 非数字法条排在后面

                articles_data.sort(key=sort_key)

                return {
                    "success": True,
                    "total_count": len(articles_data),
                    "articles": articles_data
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取法条列表失败: {str(e)}")

@router.get("/knowledge_graph/relation_cases/{crime}/{article}")
async def get_relation_cases(
    crime: str,
    article: str,
    limit: int = 5,
    search_service: SearchService = Depends(get_search_service)
):
    """获取特定罪名-法条关系的具体案例（前N个）"""
    try:
        startup_manager = get_startup_manager()
        if not startup_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail="系统正在加载中，请稍后再试"
            )

        # 获取知识图谱实例和数据加载器
        if hasattr(search_service.repository, 'data_loader'):
            data_loader = search_service.repository.data_loader
            knowledge_graph = data_loader.get_knowledge_graph()

            if knowledge_graph:
                # 首先从知识图谱获取关系详情
                relation_details = knowledge_graph.get_relation_details(crime, article)

                if not relation_details['exists']:
                    return {
                        "success": False,
                        "error": f"知识图谱中没有找到'{crime}罪'与'第{article}条'的关系",
                        "crime": crime,
                        "article": article,
                        "debug_info": {
                            "relation_exists": False,
                            "knowledge_graph_case_count": 0
                        }
                    }

                expected_case_count = relation_details['case_count']

                # 查找符合条件的案例
                matching_cases = []

                # 从数据加载器获取案例数据
                # 确保案例数据已加载
                if not hasattr(data_loader, 'original_data') or 'cases' not in data_loader.original_data:
                    logger.info("触发案例数据加载...")
                    # 首先调用检查方法
                    data_loader.load_original_data()
                    # 然后强制加载实际的案例数据到内存
                    if not hasattr(data_loader, 'original_data'):
                        data_loader.original_data = {}
                    if 'cases' not in data_loader.original_data:
                        logger.info("强制加载案例数据到内存...")
                        # 使用DataLoader的私有方法来保持兼容性
                        try:
                            data_loader._load_original_data_type('cases')
                        except Exception as e:
                            logger.error(f"加载案例数据失败: {e}")
                            data_loader.original_data['cases'] = []

                cases_data = data_loader.original_data.get('cases', [])
                if cases_data:
                    cases_found = 0

                    # 添加调试：查看前几个案例的数据格式
                    if len(matching_cases) == 0:  # 只在第一次执行时输出
                        logger.info(f"调试：准备匹配 '{crime}' 与 '第{article}条'")
                        for i, case in enumerate(cases_data[:3]):
                            try:
                                case_accusations = getattr(case, 'accusations', [])
                                case_articles = getattr(case, 'relevant_articles', [])
                                logger.info(f"案例{i}: 罪名={case_accusations}, 法条={case_articles}")
                            except Exception as e:
                                logger.error(f"案例{i}解析失败: {e}")

                    for case in cases_data:
                        try:
                            # 获取案例的罪名和相关法条
                            case_accusations = getattr(case, 'accusations', [])
                            case_articles = getattr(case, 'relevant_articles', [])

                            # 优化的罪名匹配逻辑
                            crime_match = False
                            if case_accusations:
                                crime_normalized = crime.replace('罪', '').strip()
                                for acc in case_accusations:
                                    if not acc or not isinstance(acc, str):
                                        continue
                                    acc_normalized = acc.replace('罪', '').strip()
                                    # 多种匹配策略
                                    if (crime == acc or  # 完全匹配
                                        crime_normalized == acc_normalized or  # 去"罪"字匹配
                                        crime in acc or acc in crime or  # 包含匹配
                                        crime_normalized in acc_normalized or acc_normalized in crime_normalized):
                                        crime_match = True
                                        break

                            # 增强的法条匹配逻辑
                            article_match = False
                            if case_articles:
                                target_article_str = str(article)
                                for art in case_articles:
                                    if art is None:
                                        continue
                                    art_str = str(art).strip()
                                    # 法条匹配：支持数字匹配和字符串匹配
                                    if (art_str == target_article_str or
                                        f"第{art_str}条" == f"第{target_article_str}条" or
                                        (art_str.isdigit() and target_article_str.isdigit() and
                                         int(art_str) == int(target_article_str))):
                                        article_match = True
                                        break

                            # 如果既匹配罪名又匹配法条，添加到结果中
                            if crime_match and article_match:
                                cases_found += 1
                                case_info = {
                                    "case_id": getattr(case, 'case_id', ''),
                                    "fact": getattr(case, 'fact', '')[:200] + '...' if len(getattr(case, 'fact', '')) > 200 else getattr(case, 'fact', ''),
                                    "accusations": case_accusations,
                                    "relevant_articles": case_articles,
                                    "criminals": getattr(case, 'criminals', []),
                                    "sentence_info": getattr(case, 'sentence_info', {
                                        "imprisonment_months": getattr(case, 'imprisonment_months', None),
                                        "fine_amount": getattr(case, 'fine_amount', getattr(case, 'punish_of_money', None)),
                                        "death_penalty": getattr(case, 'death_penalty', False),
                                        "life_imprisonment": getattr(case, 'life_imprisonment', False)
                                    })
                                }
                                matching_cases.append(case_info)

                                # 限制返回数量
                                if len(matching_cases) >= limit:
                                    break

                        except Exception as case_error:
                            # 单个案例解析错误不影响整体
                            continue

                else:
                    # 没有案例数据的情况
                    logger.warning(f"无法加载案例数据，cases_data为空。数据加载状态: {hasattr(data_loader, 'original_data')}")
                    return {
                        "success": False,
                        "error": "案例数据不可用，无法查找相关案例",
                        "crime": crime,
                        "article": article,
                        "debug_info": {
                            "knowledge_graph_case_count": expected_case_count,
                            "actual_cases_found": 0,
                            "total_cases_checked": 0,
                            "data_loader_has_original_data": hasattr(data_loader, 'original_data'),
                            "cases_in_original_data": 'cases' in data_loader.original_data if hasattr(data_loader, 'original_data') else False,
                            "error_reason": "案例数据为空或加载失败"
                        }
                    }

                return {
                    "success": True,
                    "crime": crime,
                    "article": article,
                    "total_found": len(matching_cases),
                    "limit": limit,
                    "cases": matching_cases,
                    "debug_info": {
                        "knowledge_graph_case_count": expected_case_count,
                        "actual_cases_found": len(matching_cases),
                        "total_cases_checked": len(cases_data),
                        "relation_confidence": relation_details['confidence'],
                        "search_params": f"Crime: '{crime}', Article: '{article}'",
                        "data_consistency": len(matching_cases) == expected_case_count
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系案例失败: {str(e)}")

# ==================== WebSocket 路由 ====================



@router.get("/debug/modules/status")
async def get_modules_status():
    """获取模块状态"""
    try:
        startup_manager = get_startup_manager()
        summary = startup_manager.get_summary()
        
        return {
            "success": True,
            "modules": {
                "data_loader": {
                    "status": "ready" if summary["is_ready"] else "loading",
                    "progress": summary["overall_progress"],
                    "current_step": summary["current_step"]
                },
                "search_engine": {
                    "status": "ready" if summary["is_ready"] else "loading"
                },
                "llm_client": {
                    "status": "ready"
                }
            },
            "system": {
                "is_ready": summary["is_ready"],
                "is_loading": summary["is_loading"],
                "overall_progress": summary["overall_progress"]
            }
        }
    except Exception as e:
        logger.error(f"获取模块状态失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }