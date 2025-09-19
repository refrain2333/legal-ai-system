#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的语义搜索引擎 - 高内聚低耦合架构
作为统一接口协调各个专业模块
"""

from typing import List, Dict, Any, Optional
import logging

from .core.search_coordinator import SearchCoordinator

logger = logging.getLogger(__name__)


class EnhancedSemanticSearch:
    """重构后的增强语义搜索引擎 - 轻量级协调器"""
    
    def __init__(self):
        """初始化搜索引擎"""
        self.data_loader = None
        self.search_coordinator = None
        self.loaded = False
    
    def _get_data_loader(self):
        """获取数据加载器"""
        if self.data_loader is None:
            from ..storage.data_loader import get_data_loader
            self.data_loader = get_data_loader()
        return self.data_loader
    
    def _get_search_coordinator(self) -> SearchCoordinator:
        """获取搜索协调器"""
        if self.search_coordinator is None:
            data_loader = self._get_data_loader()
            self.search_coordinator = SearchCoordinator(data_loader)
        return self.search_coordinator
    
    def load_data(self) -> Dict[str, Any]:
        """加载所有必需数据"""
        if self.loaded:
            return {'status': 'already_loaded'}
        
        coordinator = self._get_search_coordinator()
        success = coordinator.ensure_loaded()
        self.loaded = success
        
        if success:
            stats = coordinator.get_search_stats()
            return {
                'status': 'success',
                'total_documents': stats.get('total_documents', 0),
                'articles_count': stats.get('articles_count', 0),
                'cases_count': stats.get('cases_count', 0)
            }
        else:
            return {'status': 'failed', 'error': '数据加载失败'}
    
    def search(self, query: str, top_k: int = 10, include_content: bool = False) -> Dict[str, Any]:
        """
        执行混合搜索 - 新格式：5条法条 + 5条案例
        
        Args:
            query: 查询文本
            top_k: 总结果数量（将被分为法条和案例）
            include_content: 是否包含完整内容
            
        Returns:
            包含分类结果的字典
        """
        coordinator = self._get_search_coordinator()
        
        # 计算法条和案例的数量分配
        articles_count = min(5, top_k // 2 + 1)  # 优先保证法条数量
        cases_count = min(5, top_k - articles_count)
        
        return coordinator.execute_mixed_search(query, articles_count, cases_count, include_content)
    
    def load_more_cases(self, query: str, offset: int = 0, limit: int = 5, 
                       include_content: bool = False) -> Dict[str, Any]:
        """
        分页加载更多案例
        
        Args:
            query: 查询文本
            offset: 偏移量
            limit: 返回数量
            include_content: 是否包含完整内容
            
        Returns:
            分页案例结果
        """
        coordinator = self._get_search_coordinator()
        return coordinator.load_more_cases(query, offset, limit, include_content)
    
    def search_articles_only(self, query: str, top_k: int = 10, 
                           include_content: bool = False) -> List[Dict[str, Any]]:
        """
        只搜索法条
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            include_content: 是否包含完整内容
            
        Returns:
            法条搜索结果
        """
        coordinator = self._get_search_coordinator()
        return coordinator.search_articles_only(query, top_k, include_content)
    
    def search_cases_only(self, query: str, top_k: int = 10, 
                         include_content: bool = False) -> List[Dict[str, Any]]:
        """
        只搜索案例
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            include_content: 是否包含完整内容
            
        Returns:
            案例搜索结果
        """
        coordinator = self._get_search_coordinator()
        return coordinator.search_cases_only(query, top_k, include_content)
    
    def get_document_by_id(self, doc_id: str, include_content: bool = True) -> Optional[Dict[str, Any]]:
        """
        根据ID获取特定文档
        
        Args:
            doc_id: 文档ID
            include_content: 是否包含完整内容
            
        Returns:
            文档数据或None
        """
        coordinator = self._get_search_coordinator()
        return coordinator.get_document_by_id(doc_id, include_content)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取搜索引擎统计信息
        
        Returns:
            统计信息字典
        """
        try:
            coordinator = self._get_search_coordinator()
            return coordinator.get_search_stats()
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e), 'ready': False}
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康检查结果
        """
        try:
            coordinator = self._get_search_coordinator()
            return coordinator.health_check()
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'checks': {'engine_available': False}
            }


# 全局实例
_enhanced_search_engine = None


def get_enhanced_search_engine() -> EnhancedSemanticSearch:
    """获取增强搜索引擎实例"""
    global _enhanced_search_engine
    if _enhanced_search_engine is None:
        _enhanced_search_engine = EnhancedSemanticSearch()
        logger.info("Created new enhanced search engine instance")
    return _enhanced_search_engine


def reset_search_engine():
    """重置搜索引擎实例（主要用于测试）"""
    global _enhanced_search_engine
    _enhanced_search_engine = None
    logger.info("Search engine instance reset")