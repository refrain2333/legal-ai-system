#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领域层 (Domain Layer)
定义核心业务实体、值对象和领域服务
"""

from .entities import LegalDocument, Article, Case
from .value_objects import SearchQuery, SearchResult
from .repositories import ILegalDocumentRepository

__all__ = [
    'LegalDocument',
    'Article', 
    'Case',
    'SearchQuery',
    'SearchResult',
    'ILegalDocumentRepository'
]