#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储库接口 (Repository Interfaces)
定义领域层的数据访问接口，具体实现在基础设施层
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import LegalDocument, Article, Case
from .value_objects import SearchQuery, SearchResult, SearchContext


class ILegalDocumentRepository(ABC):
    """法律文档存储库接口"""
    
    @abstractmethod
    async def search_documents(self, query: SearchQuery) -> tuple[List[SearchResult], SearchContext]:
        """
        搜索法律文档
        
        Args:
            query: 搜索查询对象
            
        Returns:
            tuple[搜索结果列表, 搜索上下文]
        """
        pass
    
    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> Optional[LegalDocument]:
        """
        根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            法律文档对象或None
        """
        pass
    
    @abstractmethod
    async def get_documents_by_ids(self, document_ids: List[str]) -> List[LegalDocument]:
        """
        批量获取文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            文档列表
        """
        pass
    
    @abstractmethod
    def get_total_document_count(self) -> Dict[str, int]:
        """
        获取文档总数统计
        
        Returns:
            按类型统计的文档数量
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """
        检查存储库是否准备就绪
        
        Returns:
            是否可用
        """
        pass


class IArticleRepository(ABC):
    """法条存储库接口"""
    
    @abstractmethod
    async def get_article_by_number(self, article_number: int, law_name: Optional[str] = None) -> Optional[Article]:
        """根据条文号获取法条"""
        pass
    
    @abstractmethod
    async def get_articles_by_chapter(self, chapter: str, law_name: Optional[str] = None) -> List[Article]:
        """根据章节获取法条列表"""
        pass


class ICaseRepository(ABC):
    """案例存储库接口"""
    
    @abstractmethod
    async def get_cases_by_accusation(self, accusation: str) -> List[Case]:
        """根据罪名获取案例"""
        pass
    
    @abstractmethod
    async def get_cases_by_article(self, article_number: int) -> List[Case]:
        """根据法条获取相关案例"""
        pass
    
    @abstractmethod 
    async def get_severe_punishment_cases(self) -> List[Case]:
        """获取重刑案例"""
        pass