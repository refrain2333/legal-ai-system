#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律检索API路由
提供RESTful API接口供前端和其他服务调用
"""

import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path as PathParam, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio

from ..services.retrieval_service import get_retrieval_service, RetrievalService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/search", tags=["检索服务"])

# Pydantic模型定义
class SearchRequest(BaseModel):
    """检索请求模型"""
    query: str = Field(..., min_length=1, max_length=500, description="检索查询文本")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="最小相似度阈值")
    doc_types: Optional[List[str]] = Field(default=None, description="文档类型过滤，如['law', 'case']")
    include_metadata: bool = Field(default=True, description="是否包含详细元数据")

class SearchResult(BaseModel):
    """单个检索结果模型"""
    id: str = Field(..., description="文档唯一标识")
    type: str = Field(..., description="文档类型")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容摘要")
    score: float = Field(..., description="相似度分数")
    rank: int = Field(..., description="排名")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文档元数据")

class SearchResponse(BaseModel):
    """检索响应模型"""
    query: str = Field(..., description="原始查询")
    results: List[SearchResult] = Field(..., description="检索结果列表")
    total: int = Field(..., description="结果总数")
    search_time: float = Field(..., description="检索耗时（秒）")
    message: str = Field(..., description="响应消息")

class DocumentDetail(BaseModel):
    """文档详情模型"""
    id: str = Field(..., description="文档唯一标识")
    type: str = Field(..., description="文档类型")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="完整文档内容")
    score: Optional[float] = Field(default=None, description="相似度分数（如果适用）")
    rank: Optional[int] = Field(default=None, description="排名（如果适用）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文档元数据")

class StatisticsResponse(BaseModel):
    """统计信息响应模型"""
    status: str = Field(..., description="服务状态")
    total_documents: Optional[int] = Field(default=None, description="文档总数")
    law_documents: Optional[int] = Field(default=None, description="法律条文数量")
    case_documents: Optional[int] = Field(default=None, description="案例数量")
    vector_dimension: Optional[int] = Field(default=None, description="向量维度")
    service_ready: Optional[bool] = Field(default=None, description="服务是否就绪")
    index_path: Optional[str] = Field(default=None, description="索引存储路径")

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    service: str = Field(..., description="服务名称")
    status: str = Field(..., description="服务状态")
    timestamp: float = Field(..., description="检查时间戳")
    index_ready: Optional[bool] = Field(default=None, description="索引是否就绪")
    test_search: Optional[str] = Field(default=None, description="测试检索结果")

# API端点实现
@router.post("/", 
            response_model=SearchResponse,
            summary="执行智能检索",
            description="根据查询文本检索相关的法律条文和案例")
async def search_documents(
    request: SearchRequest,
    service: RetrievalService = Depends(get_retrieval_service)
) -> SearchResponse:
    """
    执行智能检索
    
    Args:
        request: 检索请求参数
        service: 检索服务实例
        
    Returns:
        检索结果
        
    Raises:
        HTTPException: 服务错误时
    """
    try:
        logger.info(f"收到检索请求: '{request.query[:50]}...' (Top-{request.top_k})")
        
        # 执行检索
        result = await service.search(
            query=request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
            doc_types=request.doc_types,
            include_metadata=request.include_metadata
        )
        
        # 转换为响应模型
        search_results = [
            SearchResult(**doc) for doc in result["results"]
        ]
        
        response = SearchResponse(
            query=result["query"],
            results=search_results,
            total=result["total"],
            search_time=result["search_time"],
            message=result["message"]
        )
        
        logger.info(f"检索完成，返回 {len(search_results)} 个结果")
        return response
        
    except Exception as e:
        logger.error(f"检索API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"检索服务错误: {str(e)}"
        )

@router.get("/quick", 
           response_model=SearchResponse,
           summary="快速检索接口",
           description="通过URL参数快速检索，适合简单调用")
async def quick_search(
    q: str = Query(..., min_length=1, max_length=500, description="检索查询文本"),
    limit: int = Query(default=10, ge=1, le=50, description="返回结果数量"),
    type: Optional[str] = Query(default=None, description="文档类型过滤，如'law'或'case'"),
    service: RetrievalService = Depends(get_retrieval_service)
) -> SearchResponse:
    """
    快速检索接口
    
    Args:
        q: 查询文本
        limit: 结果数量限制
        type: 文档类型过滤
        service: 检索服务实例
        
    Returns:
        检索结果
    """
    try:
        doc_types = [type] if type and type in ["law", "case"] else None
        
        request = SearchRequest(
            query=q,
            top_k=limit,
            doc_types=doc_types,
            include_metadata=False  # 快速检索不包含详细元数据
        )
        
        return await search_documents(request, service)
        
    except Exception as e:
        logger.error(f"快速检索API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"快速检索错误: {str(e)}"
        )

@router.get("/document/{doc_id}",
           response_model=DocumentDetail,
           summary="获取文档详情",
           description="根据文档ID获取完整文档内容")
async def get_document(
    doc_id: str = PathParam(..., description="文档唯一标识"),
    service: RetrievalService = Depends(get_retrieval_service)
) -> DocumentDetail:
    """
    获取文档详情
    
    Args:
        doc_id: 文档ID
        service: 检索服务实例
        
    Returns:
        文档详情
        
    Raises:
        HTTPException: 文档不存在或服务错误时
    """
    try:
        logger.info(f"获取文档详情: {doc_id}")
        
        document = await service.get_document_by_id(doc_id)
        
        if document is None:
            raise HTTPException(
                status_code=404,
                detail=f"文档 {doc_id} 未找到"
            )
        
        return DocumentDetail(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取文档详情错误: {str(e)}"
        )

@router.get("/statistics",
           response_model=StatisticsResponse,
           summary="获取统计信息",
           description="获取检索服务的统计信息和状态")
async def get_statistics(
    service: RetrievalService = Depends(get_retrieval_service)
) -> StatisticsResponse:
    """
    获取统计信息
    
    Args:
        service: 检索服务实例
        
    Returns:
        统计信息
    """
    try:
        stats = await service.get_statistics()
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"获取统计信息API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息错误: {str(e)}"
        )

@router.get("/health",
           response_model=HealthResponse,
           summary="健康检查",
           description="检查检索服务的健康状态")
async def health_check(
    service: RetrievalService = Depends(get_retrieval_service)
) -> HealthResponse:
    """
    健康检查
    
    Args:
        service: 检索服务实例
        
    Returns:
        健康状态
    """
    try:
        health_info = await service.health_check()
        return HealthResponse(**health_info)
        
    except Exception as e:
        logger.error(f"健康检查API错误: {e}")
        return HealthResponse(
            service="retrieval_service",
            status="unhealthy",
            timestamp=__import__('time').time(),
            error=str(e)
        )

@router.post("/rebuild",
            summary="重建索引",
            description="重新构建检索索引（管理员功能）")
async def rebuild_index(
    service: RetrievalService = Depends(get_retrieval_service)
) -> Dict[str, Any]:
    """
    重建索引
    
    Args:
        service: 检索服务实例
        
    Returns:
        重建结果
    """
    try:
        logger.info("开始重建索引...")
        success = await service.rebuild_index()
        
        if success:
            return {
                "status": "success",
                "message": "索引重建成功",
                "timestamp": __import__('time').time()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="索引重建失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重建索引API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"重建索引错误: {str(e)}"
        )

# 批量检索接口（可选扩展）
@router.post("/batch",
            response_model=List[SearchResponse],
            summary="批量检索",
            description="同时执行多个检索查询")
async def batch_search(
    requests: List[SearchRequest],
    service: RetrievalService = Depends(get_retrieval_service)
) -> List[SearchResponse]:
    """
    批量检索
    
    Args:
        requests: 检索请求列表（最多10个）
        service: 检索服务实例
        
    Returns:
        批量检索结果
    """
    try:
        if len(requests) > 10:
            raise HTTPException(
                status_code=400,
                detail="批量请求数量不能超过10个"
            )
        
        logger.info(f"收到批量检索请求: {len(requests)} 个查询")
        
        # 并行执行所有检索
        tasks = [
            search_documents(request, service) 
            for request in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量检索第 {i+1} 个查询失败: {result}")
                formatted_results.append(SearchResponse(
                    query=requests[i].query,
                    results=[],
                    total=0,
                    search_time=0.0,
                    message=f"检索失败: {str(result)}"
                ))
            else:
                formatted_results.append(result)
        
        logger.info(f"批量检索完成，处理了 {len(formatted_results)} 个查询")
        return formatted_results
        
    except Exception as e:
        logger.error(f"批量检索API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"批量检索错误: {str(e)}"
        )