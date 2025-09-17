#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
值对象 (Value Objects)
定义领域中的值对象，不可变的业务概念
"""

from dataclasses import dataclass
from typing import List, Optional
from .entities import LegalDocument


@dataclass(frozen=True)
class SearchQuery:
    """搜索查询值对象"""
    
    query_text: str
    max_results: int = 10
    similarity_threshold: float = 0.0
    document_types: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.max_results <= 0:
            object.__setattr__(self, 'max_results', 1)
        elif self.max_results > 100:
            object.__setattr__(self, 'max_results', 100)
            
        if self.similarity_threshold < 0:
            object.__setattr__(self, 'similarity_threshold', 0.0)
        elif self.similarity_threshold > 1:
            object.__setattr__(self, 'similarity_threshold', 1.0)
    
    def is_valid(self) -> bool:
        """验证查询是否有效"""
        return bool(self.query_text.strip())


@dataclass(frozen=True)
class SearchResult:
    """搜索结果值对象"""
    
    document: LegalDocument
    similarity_score: float
    rank: int = 0
    
    def __post_init__(self):
        if self.similarity_score < 0:
            object.__setattr__(self, 'similarity_score', 0.0)
        elif self.similarity_score > 1:
            object.__setattr__(self, 'similarity_score', 1.0)
    
    @property
    def is_high_confidence(self) -> bool:
        """判断是否为高置信度结果"""
        return self.similarity_score >= 0.8
    
    @property
    def confidence_level(self) -> str:
        """获取置信度等级"""
        if self.similarity_score >= 0.9:
            return "very_high"
        elif self.similarity_score >= 0.8:
            return "high"  
        elif self.similarity_score >= 0.6:
            return "medium"
        else:
            return "low"


@dataclass(frozen=True)
class SearchContext:
    """搜索上下文值对象"""
    
    total_documents_searched: int
    search_duration_ms: float
    query_vector_dimension: int = 768
    
    def get_performance_info(self) -> dict:
        """获取性能信息"""
        return {
            'documents_searched': self.total_documents_searched,
            'duration_ms': round(self.search_duration_ms, 2),
            'avg_time_per_doc': round(self.search_duration_ms / max(1, self.total_documents_searched), 4)
        }