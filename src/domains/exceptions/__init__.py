#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分层异常处理体系
定义业务相关的异常类型，支持精确的错误处理
"""

from typing import Optional, Dict, Any


class LegalSearchException(Exception):
    """法律搜索业务异常基类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于API返回"""
        return {
            "error": str(self),
            "error_code": self.error_code,
            "error_type": self.__class__.__name__,
            "details": self.details
        }


class SystemNotReadyException(LegalSearchException):
    """系统未准备就绪异常"""

    def __init__(self, loading_info: Optional[Dict] = None):
        super().__init__(
            "系统正在加载中，请稍后再试",
            "SYSTEM_NOT_READY",
            {"loading_info": loading_info}
        )


class VectorSearchException(LegalSearchException):
    """向量搜索异常"""

    def __init__(self, message: str, search_type: str = "unknown"):
        super().__init__(
            message,
            "VECTOR_SEARCH_ERROR",
            {"search_type": search_type}
        )


class ModelNotLoadedException(VectorSearchException):
    """模型未加载异常"""

    def __init__(self, model_name: str = "unknown"):
        super().__init__(
            f"模型 {model_name} 未加载或加载失败",
            "MODEL_NOT_LOADED"
        )
        self.details["model_name"] = model_name


class QueryEncodingException(VectorSearchException):
    """查询编码异常"""

    def __init__(self, query: str, reason: str = "unknown"):
        super().__init__(
            f"查询编码失败: {reason}",
            "QUERY_ENCODING_ERROR"
        )
        self.details.update({"query": query, "reason": reason})


class LLMServiceException(LegalSearchException):
    """LLM服务异常"""

    def __init__(
        self,
        message: str,
        service_name: str,
        retryable: bool = True,
        timeout: bool = False
    ):
        super().__init__(
            message,
            f"LLM_{service_name.upper()}_ERROR",
            {
                "service_name": service_name,
                "retryable": retryable,
                "timeout": timeout
            }
        )
        self.service_name = service_name
        self.retryable = retryable
        self.timeout = timeout


class LLMTimeoutException(LLMServiceException):
    """LLM服务超时异常"""

    def __init__(self, service_name: str, timeout_seconds: int):
        super().__init__(
            f"LLM服务 {service_name} 超时 ({timeout_seconds}秒)",
            service_name,
            retryable=True,
            timeout=True
        )
        self.details["timeout_seconds"] = timeout_seconds


class LLMCircuitBreakerException(LLMServiceException):
    """LLM熔断器异常"""

    def __init__(self, service_name: str, failure_count: int):
        super().__init__(
            f"LLM服务 {service_name} 已熔断 (失败次数: {failure_count})",
            service_name,
            retryable=False,
            timeout=False
        )
        self.details["failure_count"] = failure_count


class KnowledgeGraphException(LegalSearchException):
    """知识图谱异常"""

    def __init__(self, message: str, operation: str = "unknown"):
        super().__init__(
            message,
            "KNOWLEDGE_GRAPH_ERROR",
            {"operation": operation}
        )


class EntityNotFoundException(KnowledgeGraphException):
    """实体未找到异常"""

    def __init__(self, entity: str, entity_type: str = "unknown"):
        super().__init__(
            f"知识图谱中未找到实体: {entity}",
            "ENTITY_NOT_FOUND"
        )
        self.details.update({"entity": entity, "entity_type": entity_type})


class RelationNotFoundException(KnowledgeGraphException):
    """关系未找到异常"""

    def __init__(self, entity1: str, entity2: str):
        super().__init__(
            f"未找到 {entity1} 与 {entity2} 之间的关系",
            "RELATION_NOT_FOUND"
        )
        self.details.update({"entity1": entity1, "entity2": entity2})


class DataLoadException(LegalSearchException):
    """数据加载异常"""

    def __init__(self, message: str, data_type: str = "unknown"):
        super().__init__(
            message,
            "DATA_LOAD_ERROR",
            {"data_type": data_type}
        )


class ConfigurationException(LegalSearchException):
    """配置异常"""

    def __init__(self, message: str, config_key: str = "unknown"):
        super().__init__(
            message,
            "CONFIGURATION_ERROR",
            {"config_key": config_key}
        )


class ValidationException(LegalSearchException):
    """参数验证异常"""

    def __init__(self, message: str, field: str = "unknown", value: Any = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"field": field, "value": str(value) if value is not None else None}
        )


# 异常严重级别映射
EXCEPTION_SEVERITY = {
    SystemNotReadyException: "warning",
    VectorSearchException: "error",
    ModelNotLoadedException: "critical",
    QueryEncodingException: "warning",
    LLMServiceException: "warning",
    LLMTimeoutException: "warning",
    LLMCircuitBreakerException: "error",
    KnowledgeGraphException: "warning",
    EntityNotFoundException: "info",
    RelationNotFoundException: "info",
    DataLoadException: "critical",
    ConfigurationException: "critical",
    ValidationException: "warning"
}


def get_exception_severity(exception: LegalSearchException) -> str:
    """
    获取异常严重级别

    Args:
        exception: 异常实例

    Returns:
        严重级别字符串
    """
    return EXCEPTION_SEVERITY.get(type(exception), "error")