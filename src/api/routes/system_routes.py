#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统状态路由模块
包含系统状态监控和管理相关的API接口
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..models import StatusResponse
from src.services.search_service import SearchService
from src.infrastructure.repositories import get_legal_document_repository
from src.infrastructure.startup import get_startup_manager

logger = logging.getLogger(__name__)

# 创建系统状态路由器
router = APIRouter()


def get_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的搜索服务实例"""
    from src.infrastructure.llm.llm_client import LLMClient
    from src.config.settings import settings

    repository = get_legal_document_repository()
    llm_client = LLMClient(settings)
    return SearchService(repository, llm_client, debug_mode=False)


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
        logger.error(f"获取系统状态失败: {str(e)}")
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
        logger.error(f"获取启动状态失败: {str(e)}")
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
        logger.error(f"强制重新加载失败: {str(e)}")
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
        logger.error(f"获取加载步骤失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取加载步骤失败: {str(e)}"
        )


@router.get("/modules/status")
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