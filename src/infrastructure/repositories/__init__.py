#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储库基础设施模块

提供领域层存储库接口的具体实现，包括：
- 法律文档存储库实现
- 搜索和数据访问功能
"""

from .legal_document_repository import LegalDocumentRepository, get_legal_document_repository

__all__ = [
    'LegalDocumentRepository',
    'get_legal_document_repository'
]