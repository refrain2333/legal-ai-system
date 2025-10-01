#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的搜索服务核心策略
将67个方法简化为策略模式，大幅减少重复代码
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from ..domains.value_objects import SearchQuery

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """搜索策略枚举"""
    BASIC_SEMANTIC = "basic_semantic"
    MIXED_HYBRID = "mixed_hybrid"
    INTELLIGENT_DEBUG = "intelligent_debug"
    ENHANCED_MULTI = "enhanced_multi"
    KG_ENHANCED = "kg_enhanced"
    CRIME_CONSISTENCY = "crime_consistency"


class ISearchStrategy(ABC):
    """搜索策略接口"""

    def __init__(self, repository, llm_client=None):
        self.repository = repository
        self.llm_client = llm_client

    @abstractmethod
    async def execute(self, query_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索策略"""
        pass

    def _create_search_query(self, query_text: str, max_results: int) -> SearchQuery:
        """创建标准搜索查询对象"""
        return SearchQuery(
            query_text=query_text,
            max_results=max_results,
            document_types=None
        )

    def _validate_query(self, search_query: SearchQuery) -> Optional[str]:
        """验证查询有效性"""
        if not search_query.is_valid():
            return "无效的查询文本"
        return None


class BasicSemanticStrategy(ISearchStrategy):
    """基础语义搜索策略"""

    async def execute(self, query_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        max_results = params.get('max_results', 10)
        search_query = self._create_search_query(query_text, max_results)

        error = self._validate_query(search_query)
        if error:
            return {'success': False, 'error': error}

        try:
            results, context = await self.repository.search_documents(search_query)
            return {
                'success': True,
                'results': [r.to_dict() for r in results],
                'context': context.to_dict() if context else None
            }
        except Exception as e:
            logger.error(f"基础语义搜索失败: {e}")
            return {'success': False, 'error': str(e)}


class MixedHybridStrategy(ISearchStrategy):
    """混合搜索策略 - 分别返回法条和案例"""

    async def execute(self, query_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        articles_count = params.get('articles_count', 5)
        cases_count = params.get('cases_count', 5)

        search_query = self._create_search_query(query_text, articles_count + cases_count)

        error = self._validate_query(search_query)
        if error:
            return {'success': False, 'error': error}

        try:
            mixed_results = await self.repository.search_documents_mixed(
                search_query, articles_count, cases_count
            )

            return {
                'success': True,
                'articles': [r.to_dict() for r in mixed_results.get('articles', [])],
                'cases': [r.to_dict() for r in mixed_results.get('cases', [])],
                'total_articles': len(mixed_results.get('articles', [])),
                'total_cases': len(mixed_results.get('cases', []))
            }
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return {'success': False, 'error': str(e)}


class EnhancedMultiStrategy(ISearchStrategy):
    """增强多路召回策略"""

    async def execute(self, query_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        articles_count = params.get('articles_count', 5)
        cases_count = params.get('cases_count', 5)

        try:
            # 尝试使用三路召回引擎
            if hasattr(self.repository, 'multi_retrieval_engine') and self.repository.multi_retrieval_engine:
                raw_results = await self.repository.multi_retrieval_engine.three_way_retrieval(
                    query_text,
                    top_k=(articles_count + cases_count) * 2
                )

                # 分离结果
                articles_results = [r for r in raw_results if 'article' in r.get('id', '')][:articles_count]
                cases_results = [r for r in raw_results if 'case' in r.get('id', '')][:cases_count]

                return {
                    'success': True,
                    'articles': articles_results,
                    'cases': cases_results,
                    'total_articles': len(articles_results),
                    'total_cases': len(cases_results),
                    'enhancement': 'multi_retrieval'
                }
            else:
                # 降级到混合搜索
                fallback_strategy = MixedHybridStrategy(self.repository, self.llm_client)
                return await fallback_strategy.execute(query_text, params)

        except Exception as e:
            logger.error(f"增强多路召回失败: {e}")
            # 降级到混合搜索
            fallback_strategy = MixedHybridStrategy(self.repository, self.llm_client)
            return await fallback_strategy.execute(query_text, params)


class KGEnhancedStrategy(ISearchStrategy):
    """知识图谱增强搜索策略"""

    async def execute(self, query_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        articles_count = params.get('articles_count', 5)
        cases_count = params.get('cases_count', 5)

        try:
            # 尝试使用知识图谱增强引擎
            if hasattr(self.repository, 'knowledge_enhanced_engine') and self.repository.knowledge_enhanced_engine:
                raw_results = await self.repository.knowledge_enhanced_engine.kg_enhanced_search(
                    query_text,
                    top_k=articles_count + cases_count
                )

                # 处理KG增强结果
                articles_results = [r for r in raw_results if 'article' in r.get('id', '')][:articles_count]
                cases_results = [r for r in raw_results if 'case' in r.get('id', '')][:cases_count]

                return {
                    'success': True,
                    'articles': articles_results,
                    'cases': cases_results,
                    'total_articles': len(articles_results),
                    'total_cases': len(cases_results),
                    'enhancement': 'knowledge_graph'
                }
            else:
                # 降级到增强多路召回
                fallback_strategy = EnhancedMultiStrategy(self.repository, self.llm_client)
                return await fallback_strategy.execute(query_text, params)

        except Exception as e:
            logger.error(f"知识图谱增强搜索失败: {e}")
            # 降级到增强多路召回
            fallback_strategy = EnhancedMultiStrategy(self.repository, self.llm_client)
            return await fallback_strategy.execute(query_text, params)


class SearchPipeline:
    """搜索管道 - 统一搜索入口"""

    def __init__(self, repository, llm_client=None):
        self.repository = repository
        self.llm_client = llm_client
        self.strategies = {
            SearchStrategy.BASIC_SEMANTIC: BasicSemanticStrategy(repository, llm_client),
            SearchStrategy.MIXED_HYBRID: MixedHybridStrategy(repository, llm_client),
            SearchStrategy.ENHANCED_MULTI: EnhancedMultiStrategy(repository, llm_client),
            SearchStrategy.KG_ENHANCED: KGEnhancedStrategy(repository, llm_client),
        }

    async def search(self, strategy: SearchStrategy, query_text: str, **params) -> Dict[str, Any]:
        """统一搜索入口"""
        start_time = time.time()

        try:
            strategy_impl = self.strategies.get(strategy)
            if not strategy_impl:
                return {'success': False, 'error': f'未知搜索策略: {strategy}'}

            result = await strategy_impl.execute(query_text, params)

            # 添加通用的性能指标
            result['processing_time'] = round((time.time() - start_time) * 1000, 2)
            result['strategy'] = strategy.value

            return result

        except Exception as e:
            logger.error(f"搜索管道执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': round((time.time() - start_time) * 1000, 2),
                'strategy': strategy.value
            }


class SearchResultProcessor:
    """搜索结果处理器 - 统一结果转换"""

    @staticmethod
    def convert_domain_to_api(result) -> Dict[str, Any]:
        """将领域对象转换为API格式"""
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        return result

    @staticmethod
    def apply_confidence_scoring(results: List[Dict], base_confidence: float = 0.8) -> List[Dict]:
        """应用置信度评分"""
        for i, result in enumerate(results):
            # 基于排序位置的置信度衰减
            position_factor = max(0.3, 1.0 - (i * 0.1))
            result['confidence'] = round(base_confidence * position_factor, 3)
        return results

    @staticmethod
    def create_error_response(error_message: str) -> Dict[str, Any]:
        """创建统一的错误响应"""
        return {
            'success': False,
            'error': error_message,
            'articles': [],
            'cases': [],
            'total_articles': 0,
            'total_cases': 0
        }