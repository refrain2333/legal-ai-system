#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律文档存储库实现
实现领域层定义的存储库接口，组合搜索引擎和数据加载器
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple

from ...domains.entities import LegalDocument, Article, Case
from ...domains.value_objects import SearchQuery, SearchResult, SearchContext
from ...domains.repositories import ILegalDocumentRepository
from ..search.vector_search_engine import EnhancedSemanticSearch
from ..storage.data_loader import get_data_loader

logger = logging.getLogger(__name__)


class LegalDocumentRepository(ILegalDocumentRepository):
    """法律文档存储库具体实现"""
    
    def __init__(self):
        """初始化存储库"""
        self.search_engine = EnhancedSemanticSearch()
        self.data_loader = get_data_loader()
        self.multi_retrieval_engine = None  # 多路召回引擎
        self.kg_enhanced_engine = None      # 知识图谱增强引擎
        self._initialized = False
    
    async def search_documents(self, query: SearchQuery) -> Tuple[List[SearchResult], SearchContext]:
        """搜索法律文档"""
        start_time = time.time()
        
        try:
            # 确保数据已加载
            if not self._initialized:
                await self._initialize()
            
            # 执行底层搜索 - 获取基础搜索结果（ID和相似度）
            raw_results = self.search_engine.search(
                query.query_text, 
                query.max_results, 
                include_content=True  # 直接加载完整内容
            )
            
            # 转换为领域对象
            domain_results = []
            for i, raw_result in enumerate(raw_results):
                # 过滤低相似度结果
                if raw_result['similarity'] < query.similarity_threshold:
                    continue
                
                # 获取完整文档信息
                document = await self._convert_raw_to_domain_document(raw_result)
                if document is None:
                    continue
                
                # 创建搜索结果值对象
                search_result = SearchResult(
                    document=document,
                    similarity_score=raw_result['similarity'],
                    rank=i + 1
                )
                domain_results.append(search_result)
            
            # 创建搜索上下文
            end_time = time.time()
            context = SearchContext(
                total_documents_searched=self.data_loader.get_total_document_count(),
                search_duration_ms=(end_time - start_time) * 1000
            )
            
            return domain_results, context
            
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}", exc_info=True)
            raise
    
    async def get_document_by_id(self, document_id: str) -> Optional[LegalDocument]:
        """根据ID获取文档"""
        try:
            if not self._initialized:
                await self._initialize()
            
            # 使用搜索引擎的get_document_by_id方法
            raw_doc = self.search_engine.get_document_by_id(document_id, include_content=True)
            if raw_doc is None:
                return None
            
            return await self._convert_raw_to_domain_document(raw_doc)
            
        except Exception as e:
            logger.error(f"获取文档失败 (ID: {document_id}): {str(e)}")
            return None
    
    async def get_documents_by_ids(self, document_ids: List[str]) -> List[LegalDocument]:
        """批量获取文档"""
        documents = []
        for doc_id in document_ids:
            doc = await self.get_document_by_id(doc_id)
            if doc is not None:
                documents.append(doc)
        return documents
    
    def get_total_document_count(self) -> Dict[str, int]:
        """获取文档总数统计"""
        try:
            stats = self.search_engine.get_stats()
            return {
                'articles': stats.get('articles_count', 0),
                'cases': stats.get('cases_count', 0),
                'total': stats.get('total_documents', 0)
            }
        except Exception as e:
            logger.error(f"获取文档统计失败: {str(e)}")
            return {'articles': 0, 'cases': 0, 'total': 0}
    
    def is_ready(self) -> bool:
        """检查存储库是否准备就绪"""
        try:
            stats = self.search_engine.get_stats()
            return stats.get('ready', False)
        except:
            return False
    
    async def search_documents_mixed(self, query: SearchQuery, articles_count: int, cases_count: int) -> Dict[str, Any]:
        """混合搜索 - 分别返回法条和案例"""
        start_time = time.time()
        
        try:
            # 确保数据已加载
            if not self._initialized:
                await self._initialize()
            
            # 调用搜索引擎的混合搜索
            search_result = self.search_engine.search(
                query=query.query_text,
                top_k=articles_count + cases_count,
                include_content=True
            )
            
            # 检查是否成功
            if not search_result.get('success', True):
                return {
                    'success': False,
                    'error': search_result.get('error', '搜索失败'),
                    'articles': [],
                    'cases': []
                }
            
            # 转换结果为领域对象
            domain_articles = []
            domain_cases = []
            
            # 处理法条结果
            for raw_result in search_result.get('articles', []):
                if raw_result['similarity'] < query.similarity_threshold:
                    continue
                    
                document = await self._convert_raw_to_domain_document(raw_result)
                if document:
                    search_result_obj = SearchResult(
                        document=document,
                        similarity_score=raw_result['similarity'],
                        rank=len(domain_articles) + 1
                    )
                    domain_articles.append(search_result_obj)
            
            # 处理案例结果
            for raw_result in search_result.get('cases', []):
                if raw_result['similarity'] < query.similarity_threshold:
                    continue
                    
                document = await self._convert_raw_to_domain_document(raw_result)
                if document:
                    search_result_obj = SearchResult(
                        document=document,
                        similarity_score=raw_result['similarity'],
                        rank=len(domain_cases) + 1
                    )
                    domain_cases.append(search_result_obj)
            
            end_time = time.time()
            return {
                'success': True,
                'articles': domain_articles,
                'cases': domain_cases,
                'total_articles': len(domain_articles),
                'total_cases': len(domain_cases),
                'query': query.query_text,
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2),
                    'articles_requested': articles_count,
                    'cases_requested': cases_count
                }
            }
            
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'articles': [],
                'cases': []
            }
    
    async def load_more_cases(self, query: SearchQuery, offset: int, limit: int) -> Dict[str, Any]:
        """分页加载更多案例"""
        start_time = time.time()
        
        try:
            # 确保数据已加载
            if not self._initialized:
                await self._initialize()
            
            # 调用搜索引擎的分页案例搜索
            search_result = self.search_engine.load_more_cases(
                query=query.query_text,
                offset=offset,
                limit=limit,
                include_content=True
            )
            
            # 检查是否成功
            if not search_result.get('success', True):
                return {
                    'success': False,
                    'error': search_result.get('error', '加载失败'),
                    'cases': []
                }
            
            # 转换结果为领域对象
            domain_cases = []
            for raw_result in search_result.get('cases', []):
                if raw_result['similarity'] < query.similarity_threshold:
                    continue
                    
                document = await self._convert_raw_to_domain_document(raw_result)
                if document:
                    search_result_obj = SearchResult(
                        document=document,
                        similarity_score=raw_result['similarity'],
                        rank=offset + len(domain_cases) + 1
                    )
                    domain_cases.append(search_result_obj)
            
            end_time = time.time()
            return {
                'success': True,
                'cases': domain_cases,
                'offset': offset,
                'limit': limit,
                'returned_count': len(domain_cases),
                'has_more': search_result.get('has_more', False),
                'query': query.query_text,
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"分页加载案例失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'cases': []
            }
    
    async def _initialize(self):
        """初始化存储库"""
        if self._initialized:
            return

        try:
            # 加载搜索引擎数据
            load_result = self.search_engine.load_data()
            if load_result.get('status') not in ['success', 'partial', 'already_loaded']:
                raise RuntimeError(f"搜索引擎初始化失败: {load_result}")

            # 尝试初始化多路召回引擎和知识图谱增强引擎
            await self._initialize_advanced_engines()

            self._initialized = True
            logger.info("法律文档存储库初始化成功")

        except Exception as e:
            logger.error(f"存储库初始化失败: {str(e)}")
            raise

    async def _initialize_advanced_engines(self):
        """初始化高级搜索引擎"""
        try:
            from ...config.settings import settings

            # 初始化多路召回引擎
            if hasattr(self.data_loader, 'multi_retrieval_engine') and self.data_loader.multi_retrieval_engine:
                self.multi_retrieval_engine = self.data_loader.multi_retrieval_engine
                logger.info("多路召回引擎已连接")
            else:
                logger.info("多路召回引擎不可用，将使用基础搜索")

            # 初始化知识图谱增强引擎
            knowledge_graph = self.data_loader.get_knowledge_graph()
            if knowledge_graph:
                from ..search.knowledge_enhanced_engine import KnowledgeEnhancedSearchEngine

                if self.multi_retrieval_engine:
                    self.kg_enhanced_engine = KnowledgeEnhancedSearchEngine(
                        self.multi_retrieval_engine,
                        knowledge_graph,
                        settings
                    )
                    logger.info("知识图谱增强引擎初始化成功")
                else:
                    logger.warning("多路召回引擎不可用，无法初始化知识图谱增强引擎")
            else:
                logger.info("知识图谱不可用，将使用标准搜索")

        except Exception as e:
            logger.warning(f"高级搜索引擎初始化失败: {e}")
            # 不抛出异常，允许使用基础搜索功能
    
    async def _convert_raw_to_domain_document(self, raw_result: Dict[str, Any]) -> Optional[LegalDocument]:
        """将原始搜索结果转换为领域文档对象"""
        try:
            doc_type = raw_result.get('type')
            doc_id = raw_result.get('id', '')
            title = raw_result.get('title', '')
            
            # 获取完整内容
            content = await self._get_full_content(raw_result)
            
            # 支持新旧格式的类型判断
            if doc_type in ['articles', 'article']:
                return Article(
                    id=doc_id,
                    title=title,
                    content=content,
                    document_type='article',
                    article_number=raw_result.get('article_number'),
                    chapter=raw_result.get('chapter'),
                    law_name=raw_result.get('law_name', '中华人民共和国刑法')
                )
            elif doc_type in ['cases', 'case']:
                return Case(
                    id=doc_id,
                    title=title,
                    content=content,
                    document_type='case',
                    case_id=raw_result.get('case_id'),
                    criminals=raw_result.get('criminals'),
                    accusations=raw_result.get('accusations'),
                    relevant_articles=raw_result.get('relevant_articles'),
                    punish_of_money=raw_result.get('punish_of_money'),
                    death_penalty=raw_result.get('death_penalty'),
                    life_imprisonment=raw_result.get('life_imprisonment'),
                    imprisonment_months=raw_result.get('imprisonment_months')
                )
            else:
                logger.warning(f"未知文档类型: {doc_type}")
                return None
                
        except Exception as e:
            logger.error(f"转换文档失败: {str(e)}, raw_result: {raw_result}")
            return None
    
    async def _get_full_content(self, raw_result: Dict[str, Any]) -> str:
        """获取文档完整内容"""
        # 如果已经有content字段，直接返回
        if 'content' in raw_result and raw_result['content']:
            return raw_result['content']
        
        doc_type = raw_result.get('type')
        doc_id = raw_result.get('id', '')
        
        try:
            # 支持新旧格式的类型判断
            if doc_type in ['articles', 'article']:
                content = self.data_loader.get_article_content(doc_id)
            elif doc_type in ['cases', 'case']:
                case_id = raw_result.get('case_id') or doc_id
                content = self.data_loader.get_case_content(case_id)
                
                # 如果失败，尝试其他ID格式
                if not content and case_id.startswith('case_case_'):
                    alt_case_id = case_id.replace('case_case_', 'case_')
                    content = self.data_loader.get_case_content(alt_case_id)
            else:
                content = ''
            
            return content or '内容加载失败'
            
        except Exception as e:
            logger.error(f"加载文档内容失败: {str(e)}")
            return '内容加载失败'


# 全局实例
_repository_instance = None

def get_legal_document_repository() -> LegalDocumentRepository:
    """获取法律文档存储库实例"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = LegalDocumentRepository()
    return _repository_instance