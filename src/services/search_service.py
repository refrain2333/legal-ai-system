#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索服务 (Search Service)
封装搜索业务逻辑，解耦API层和基础设施层
"""

import time
from typing import List, Optional, Dict, Any
import logging

from ..domains.entities import LegalDocument, Article, Case
from ..domains.value_objects import SearchQuery, SearchResult, SearchContext
from ..domains.repositories import ILegalDocumentRepository

logger = logging.getLogger(__name__)


class SearchService:
    """搜索业务服务类 - 业务逻辑核心"""
    
    def __init__(self, repository: ILegalDocumentRepository):
        """
        初始化搜索服务
        
        Args:
            repository: 法律文档存储库实现
        """
        self.repository = repository
    
    async def search_documents(self, query_text: str, max_results: int = 10, 
                             document_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        搜索法律文档 - 完整业务流程
        
        Args:
            query_text: 查询文本
            max_results: 最大结果数
            document_types: 文档类型过滤
            
        Returns:
            包含搜索结果和元信息的字典
        """
        start_time = time.time()
        
        try:
            # 1. 创建搜索查询值对象
            search_query = SearchQuery(
                query_text=query_text,
                max_results=max_results,
                document_types=document_types
            )
            
            # 2. 验证查询有效性
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")
            
            # 3. 执行搜索
            results, context = await self.repository.search_documents(search_query)
            
            # 4. 转换为API响应格式
            api_results = []
            for result in results:
                api_result = self._convert_domain_result_to_api(result)
                api_results.append(api_result)
            
            # 5. 构建响应
            end_time = time.time()
            response = {
                'success': True,
                'results': api_results,
                'total': len(api_results),
                'query': query_text,
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2),
                    'total_documents_searched': context.total_documents_searched,
                    'performance_info': context.get_performance_info()
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"搜索服务错误: {str(e)}", exc_info=True)
            return self._create_error_response(f"搜索失败: {str(e)}")
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单个文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息字典或None
        """
        try:
            document = await self.repository.get_document_by_id(document_id)
            if document is None:
                return None
            
            return self._convert_domain_document_to_api(document)
            
        except Exception as e:
            logger.error(f"获取文档失败 (ID: {document_id}): {str(e)}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        try:
            is_ready = self.repository.is_ready()
            document_counts = self.repository.get_total_document_count()
            
            return {
                'status': 'ok' if is_ready else 'not_ready',
                'ready': is_ready,
                'total_documents': document_counts.get('total', 0),
                'document_breakdown': document_counts
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                'status': 'error',
                'ready': False,
                'total_documents': 0,
                'error': str(e)
            }
    
    def _convert_domain_result_to_api(self, domain_result: SearchResult) -> Dict[str, Any]:
        """将领域搜索结果转换为API格式"""
        document = domain_result.document
        
        base_result = {
            'id': document.id,
            'title': document.get_display_title(),
            'content': document.content,
            'similarity': domain_result.similarity_score,
            'type': document.document_type,
            'confidence_level': domain_result.confidence_level,
            'rank': domain_result.rank
        }
        
        # 添加类型特定字段
        if isinstance(document, Case):
            base_result.update({
                'case_id': document.case_id,
                'criminals': document.criminals,
                'accusations': document.accusations,
                'relevant_articles': document.relevant_articles,
                'punish_of_money': document.punish_of_money,
                'death_penalty': document.death_penalty,
                'life_imprisonment': document.life_imprisonment,
                'imprisonment_months': document.imprisonment_months,
                'is_severe_case': document.has_severe_punishment()
            })
        elif isinstance(document, Article):
            base_result.update({
                'article_number': document.article_number,
                'chapter': document.chapter,
                'law_name': document.law_name
            })
        
        return base_result
    
    def _convert_domain_document_to_api(self, document: LegalDocument) -> Dict[str, Any]:
        """将领域文档实体转换为API格式"""
        base_doc = {
            'id': document.id,
            'title': document.get_display_title(),
            'content': document.content,
            'type': document.document_type,
            'searchable_text': document.get_searchable_text()
        }
        
        # 添加类型特定字段
        if isinstance(document, Case):
            base_doc.update({
                'case_id': document.case_id,
                'criminals': document.criminals,
                'accusations': document.accusations,
                'relevant_articles': document.relevant_articles,
                'punish_of_money': document.punish_of_money,
                'death_penalty': document.death_penalty,
                'life_imprisonment': document.life_imprisonment,
                'imprisonment_months': document.imprisonment_months
            })
        elif isinstance(document, Article):
            base_doc.update({
                'article_number': document.article_number,
                'chapter': document.chapter,
                'law_name': document.law_name
            })
        
        return base_doc
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'success': False,
            'results': [],
            'total': 0,
            'query': '',
            'error': error_message
        }