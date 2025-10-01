#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础搜索路由模块
包含核心搜索功能的API接口
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from ..models import SearchRequest, SearchResponse, SearchResult
from src.services.search_service import SearchService
from src.services.factories import SearchResponseFactory
from src.infrastructure.repositories import get_legal_document_repository
from src.infrastructure.startup import get_startup_manager

logger = logging.getLogger(__name__)

# 创建搜索路由器
router = APIRouter()


def get_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的搜索服务实例"""
    from src.infrastructure.llm.llm_client import LLMClient
    from src.config.settings import settings

    repository = get_legal_document_repository()
    llm_client = LLMClient(settings)
    return SearchService(repository, llm_client, debug_mode=False)


def _format_search_response(service_result: Dict[str, Any], query: str) -> SearchResponse:
    """
    使用工厂模式的统一响应格式化函数
    大幅简化了原有的重复代码

    Args:
        service_result: 服务层返回的结果
        query: 查询文本

    Returns:
        标准的SearchResponse对象
    """
    return SearchResponseFactory.create_mixed_response(service_result, query)


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


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, search_service: SearchService = Depends(get_search_service)):
    """基础搜索接口 - 新格式：5条法条 + 5条案例"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

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

        # 使用统一的格式化函数
        return _format_search_response(service_result, request.query)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索服务错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.get("/search/cases/more")
async def load_more_cases(
    query: str,
    offset: int = 0,
    limit: int = 5,
    search_service: SearchService = Depends(get_search_service)
):
    """分页加载更多案例"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

        # 调用服务层加载更多案例
        service_result = await search_service.load_more_cases(query, offset, limit)

        if not service_result.get('success', False):
            raise HTTPException(
                status_code=400,
                detail=service_result.get('error', '加载失败')
            )

        # 使用工厂模式转换为API响应格式
        api_cases = []
        for item in service_result.get('cases', []):
            api_cases.append(SearchResponseFactory.create_mixed_response(
                {'cases': [item]}, query
            ).results[0])

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
        logger.error(f"加载更多案例错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载更多案例错误: {str(e)}")


@router.get("/document/{document_id}")
async def get_document_by_id(
    document_id: str,
    search_service: SearchService = Depends(get_search_service)
):
    """根据ID获取单个文档"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

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
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")