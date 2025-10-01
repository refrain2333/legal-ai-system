#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常处理器
为FastAPI应用提供分层的异常处理机制
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from src.domains.exceptions import (
    LegalSearchException,
    SystemNotReadyException,
    LLMServiceException,
    LLMTimeoutException,
    LLMCircuitBreakerException,
    KnowledgeGraphException,
    EntityNotFoundException,
    VectorSearchException,
    ModelNotLoadedException,
    ValidationException,
    get_exception_severity
)

logger = logging.getLogger(__name__)


async def legal_search_exception_handler(
    request: Request,
    exc: LegalSearchException
) -> JSONResponse:
    """
    统一业务异常处理器

    Args:
        request: FastAPI请求对象
        exc: 业务异常实例

    Returns:
        JSON错误响应
    """
    # 记录异常日志
    severity = get_exception_severity(exc)
    log_message = f"业务异常 [{severity.upper()}]: {str(exc)}"

    if severity == "critical":
        logger.error(log_message, exc_info=True)
    elif severity == "error":
        logger.error(log_message)
    elif severity == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)

    # 根据异常类型确定HTTP状态码
    status_code = _get_http_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            **exc.to_dict(),
            "request_path": str(request.url.path),
            "severity": severity
        }
    )


async def system_not_ready_exception_handler(
    request: Request,
    exc: SystemNotReadyException
) -> JSONResponse:
    """系统未准备就绪异常处理器"""
    logger.warning(f"系统未就绪访问: {request.url.path}")

    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": str(exc),
            "error_code": exc.error_code,
            "loading_info": exc.details.get("loading_info", {}),
            "retry_after": 5  # 建议5秒后重试
        }
    )


async def llm_service_exception_handler(
    request: Request,
    exc: LLMServiceException
) -> JSONResponse:
    """LLM服务异常处理器"""
    # 根据异常类型记录不同级别的日志
    if isinstance(exc, LLMCircuitBreakerException):
        logger.error(f"LLM服务熔断: {exc.service_name}")
        status_code = 503
    elif isinstance(exc, LLMTimeoutException):
        logger.warning(f"LLM服务超时: {exc.service_name}")
        status_code = 504
    else:
        logger.warning(f"LLM服务异常: {str(exc)}")
        status_code = 503 if exc.retryable else 400

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": str(exc),
            "error_code": exc.error_code,
            "service_name": exc.service_name,
            "retryable": exc.retryable,
            "timeout": exc.timeout,
            "suggested_action": _get_llm_suggested_action(exc)
        }
    )


async def knowledge_graph_exception_handler(
    request: Request,
    exc: KnowledgeGraphException
) -> JSONResponse:
    """知识图谱异常处理器"""
    logger.info(f"知识图谱异常: {str(exc)}")

    if isinstance(exc, (EntityNotFoundException, RelationNotFoundException)):
        status_code = 404
    else:
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            **exc.to_dict(),
            "suggestions": _get_kg_suggestions(exc)
        }
    )


async def vector_search_exception_handler(
    request: Request,
    exc: VectorSearchException
) -> JSONResponse:
    """向量搜索异常处理器"""
    if isinstance(exc, ModelNotLoadedException):
        logger.error(f"模型未加载: {str(exc)}")
        status_code = 503
    else:
        logger.warning(f"向量搜索异常: {str(exc)}")
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            **exc.to_dict(),
            "fallback_available": not isinstance(exc, ModelNotLoadedException)
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationException
) -> JSONResponse:
    """参数验证异常处理器"""
    logger.info(f"参数验证失败: {str(exc)}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            **exc.to_dict(),
            "validation_help": _get_validation_help(exc)
        }
    )


def _get_http_status_code(exc: LegalSearchException) -> int:
    """根据异常类型确定HTTP状态码"""
    if isinstance(exc, SystemNotReadyException):
        return 503
    elif isinstance(exc, LLMServiceException):
        return 503 if exc.retryable else 400
    elif isinstance(exc, (EntityNotFoundException, RelationNotFoundException)):
        return 404
    elif isinstance(exc, ModelNotLoadedException):
        return 503
    elif isinstance(exc, ValidationException):
        return 422
    else:
        return 400


def _get_llm_suggested_action(exc: LLMServiceException) -> str:
    """获取LLM异常的建议操作"""
    if isinstance(exc, LLMCircuitBreakerException):
        return "LLM服务暂时不可用，请稍后重试或使用基础搜索功能"
    elif isinstance(exc, LLMTimeoutException):
        return "LLM服务响应超时，建议简化查询或稍后重试"
    elif exc.retryable:
        return "LLM服务临时异常，建议重试"
    else:
        return "LLM服务异常，建议使用基础搜索功能"


def _get_kg_suggestions(exc: KnowledgeGraphException) -> list:
    """获取知识图谱异常的建议"""
    if isinstance(exc, EntityNotFoundException):
        return [
            "检查实体名称拼写是否正确",
            "尝试使用相关的同义词",
            "使用基础搜索功能"
        ]
    elif isinstance(exc, RelationNotFoundException):
        return [
            "该实体之间可能不存在直接关系",
            "尝试查看单个实体的相关信息",
            "使用基础搜索功能"
        ]
    else:
        return ["使用基础搜索功能作为替代"]


def _get_validation_help(exc: ValidationException) -> Dict[str, str]:
    """获取参数验证的帮助信息"""
    field = exc.details.get("field", "unknown")

    help_map = {
        "query": "查询文本不能为空，长度应在1-500字符之间",
        "top_k": "返回结果数量应在1-100之间",
        "similarity_threshold": "相似度阈值应在0.0-1.0之间",
        "offset": "偏移量应为非负整数",
        "limit": "限制数量应在1-100之间"
    }

    return {
        "field": field,
        "help": help_map.get(field, "请检查参数格式和取值范围")
    }