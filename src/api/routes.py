#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的API路由 - 包含启动状态监控
遵循分层架构原则，仅调用服务层
"""

from fastapi import APIRouter, HTTPException, Depends
from .models import SearchRequest, SearchResponse, StatusResponse, SearchResult
from ..services.search_service import SearchService
from ..infrastructure.repositories import get_legal_document_repository
from ..infrastructure.startup import get_startup_manager

# 创建路由器
router = APIRouter()

def get_search_service() -> SearchService:
    """依赖注入：获取搜索服务实例"""
    repository = get_legal_document_repository()
    return SearchService(repository)

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