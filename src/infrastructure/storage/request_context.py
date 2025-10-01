#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求上下文管理器
为每个请求创建独立的上下文，避免并发数据污染
"""

import uuid
from typing import Dict, Any, Optional
from contextvars import ContextVar
from dataclasses import dataclass, field

# 使用contextvars提供请求级别的隔离
_request_context: ContextVar[Optional['RequestContext']] = ContextVar('request_context', default=None)


@dataclass
class RequestContext:
    """请求上下文，存储请求相关的临时数据"""

    # 请求唯一标识
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 用户查询
    query: str = ""

    # 临时缓存（仅在此请求生命周期内有效）
    temp_cache: Dict[str, Any] = field(default_factory=dict)

    # 搜索路径追踪
    search_path: list = field(default_factory=list)

    # 中间结果存储
    intermediate_results: Dict[str, Any] = field(default_factory=dict)

    # LLM生成的内容
    llm_outputs: Dict[str, str] = field(default_factory=dict)

    # 性能指标
    metrics: Dict[str, float] = field(default_factory=dict)

    def add_to_path(self, step: str):
        """添加搜索步骤到路径"""
        self.search_path.append({
            'step': step,
            'timestamp': time.time()
        })

    def set_intermediate(self, key: str, value: Any):
        """存储中间结果"""
        self.intermediate_results[key] = value

    def get_intermediate(self, key: str, default=None):
        """获取中间结果"""
        return self.intermediate_results.get(key, default)

    def cache_result(self, key: str, value: Any):
        """缓存结果（仅在请求内有效）"""
        self.temp_cache[key] = value

    def get_cached(self, key: str, default=None):
        """从缓存获取结果"""
        return self.temp_cache.get(key, default)


def create_request_context(query: str = "") -> RequestContext:
    """创建新的请求上下文"""
    context = RequestContext(query=query)
    _request_context.set(context)
    return context


def get_current_context() -> Optional[RequestContext]:
    """获取当前请求上下文"""
    return _request_context.get()


def clear_context():
    """清理当前上下文"""
    _request_context.set(None)


class RequestContextMiddleware:
    """FastAPI中间件，自动管理请求上下文"""

    async def __call__(self, request, call_next):
        # 创建请求上下文
        context = create_request_context()

        try:
            # 处理请求
            response = await call_next(request)
            return response
        finally:
            # 清理上下文
            clear_context()


import time