#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索协调器
协调各个组件完成搜索任务
"""

from typing import List, Dict, Any, Optional
import logging

from .vector_calculator import VectorCalculator
from .similarity_ranker import SimilarityRanker
from ..processors.result_formatter import ResultFormatter
from ..processors.content_enricher import ContentEnricher
from ..processors.content_length_filter import ContentLengthFilter

logger = logging.getLogger(__name__)


class SearchCoordinator:
    """搜索协调器 - 协调各个模块完成搜索任务"""
    
    def __init__(self, data_loader):
        """
        初始化搜索协调器
        
        Args:
            data_loader: 数据加载器实例
        """
        self.data_loader = data_loader
        
        # 初始化各个组件
        self.vector_calculator = VectorCalculator(data_loader)
        self.similarity_ranker = SimilarityRanker()
        self.result_formatter = ResultFormatter()
        self.content_enricher = ContentEnricher(data_loader)
        self.content_filter = ContentLengthFilter(min_content_length=20)  # 设置20字符最小长度
        
        self.loaded = False
    
    def ensure_loaded(self) -> bool:
        """
        确保所有必需数据已加载
        
        Returns:
            是否加载成功
        """
        if self.loaded:
            return True
        
        try:
            # 加载向量数据和模型
            vector_stats = self.data_loader.load_vectors()
            model_stats = self.data_loader.load_model()
            
            vector_success = vector_stats.get('status') in ['success', 'already_loaded']
            model_success = model_stats.get('status') in ['success', 'already_loaded']
            
            self.loaded = vector_success and model_success
            
            if self.loaded:
                logger.info("Search coordinator loaded successfully")
            else:
                logger.error(f"Search coordinator load failed: vectors={vector_success}, model={model_success}")
            
            return self.loaded
            
        except Exception as e:
            logger.error(f"Error loading search coordinator: {e}")
            return False
    
    def execute_mixed_search(self, query: str, articles_count: int = 5, 
                           cases_count: int = 5, include_content: bool = False) -> Dict[str, Any]:
        """
        执行混合搜索 - 固定格式：先法条后案例
        
        Args:
            query: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量
            include_content: 是否包含完整内容
            
        Returns:
            包含分类结果的字典
        """
        if not self.ensure_loaded():
            logger.error("Search coordinator not ready")
            return {'success': False, 'error': 'System not ready'}
        
        try:
            # 1. 编码查询
            query_vector = self.vector_calculator.encode_query(query)
            if query_vector is None:
                logger.error("Failed to encode query")
                return {'success': False, 'error': 'Query encoding failed'}
            
            # 2. 分别搜索法条和案例
            articles_results = self._search_in_single_type(query_vector, 'articles', articles_count * 2)  # 获取更多以备过滤
            cases_results = self._search_in_single_type(query_vector, 'cases', cases_count * 2)
            
            # 3. 格式化和过滤
            formatted_articles = self._format_and_filter_results(articles_results, articles_count, include_content)
            formatted_cases = self._format_and_filter_results(cases_results, cases_count, include_content)
            
            return {
                'success': True,
                'articles': formatted_articles,
                'cases': formatted_cases,
                'total_articles': len(formatted_articles),
                'total_cases': len(formatted_cases),
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Mixed search execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_and_filter_results(self, raw_results: List[Dict[str, Any]], 
                                 target_count: int, include_content: bool) -> List[Dict[str, Any]]:
        """
        格式化和过滤结果
        
        Args:
            raw_results: 原始搜索结果
            target_count: 目标数量
            include_content: 是否包含内容
            
        Returns:
            格式化并过滤后的结果列表
        """
        # 格式化结果
        formatted_results = []
        for result in raw_results:
            formatted_result = self.result_formatter.format_single_document(result, include_content=False)
            if formatted_result:
                formatted_results.append(formatted_result)
        
        # 内容增强和长度过滤
        if include_content:
            # 获取更多候选以备过滤
            candidates = formatted_results[:target_count * 2]
            
            # 增强内容并过滤
            enriched_candidates = self.content_enricher.enrich_results_with_content(
                candidates, True, min_content_length=20
            )
            
            # 返回目标数量的结果
            return enriched_candidates[:target_count]
        else:
            # 不包含内容时直接返回目标数量
            return formatted_results[:target_count]
    
    def load_more_cases(self, query: str, offset: int = 0, limit: int = 5, 
                       include_content: bool = False) -> Dict[str, Any]:
        """
        分页加载更多案例
        
        Args:
            query: 查询文本
            offset: 偏移量（跳过的数量）
            limit: 返回数量
            include_content: 是否包含完整内容
            
        Returns:
            包含案例结果的字典
        """
        if not self.ensure_loaded():
            logger.error("Search coordinator not ready")
            return {'success': False, 'error': 'System not ready'}
        
        try:
            # 编码查询
            query_vector = self.vector_calculator.encode_query(query)
            if query_vector is None:
                logger.error("Failed to encode query")
                return {'success': False, 'error': 'Query encoding failed'}
            
            # 搜索案例，获取更多结果以支持分页和过滤
            total_needed = offset + limit * 3  # 获取更多以备过滤
            cases_results = self._search_in_single_type(query_vector, 'cases', total_needed)
            
            # 格式化和过滤
            all_formatted_cases = self._format_and_filter_results(cases_results, total_needed, include_content)
            
            # 应用分页
            paginated_cases = all_formatted_cases[offset:offset + limit]
            
            return {
                'success': True,
                'cases': paginated_cases,
                'offset': offset,
                'limit': limit,
                'returned_count': len(paginated_cases),
                'has_more': len(all_formatted_cases) > offset + limit,
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Load more cases error: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_search(self, query: str, top_k: int = 10, 
                      include_content: bool = False,
                      search_types: Optional[List[str]] = None,
                      merge_strategy: str = 'interleaved') -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            include_content: 是否包含完整内容
            search_types: 搜索类型列表 ['articles', 'cases'], None表示搜索所有
            merge_strategy: 合并策略
            
        Returns:
            搜索结果列表
        """
        if not self.ensure_loaded():
            logger.error("Search coordinator not ready")
            return []
        
        # 默认搜索所有类型
        if search_types is None:
            search_types = ['articles', 'cases']
        
        try:
            # 1. 编码查询
            query_vector = self.vector_calculator.encode_query(query)
            if query_vector is None:
                logger.error("Failed to encode query")
                return []
            
            # 2. 分别在各类型中搜索
            all_results = []
            type_results = {}
            
            for search_type in search_types:
                results = self._search_in_single_type(query_vector, search_type, top_k // len(search_types) + 1)
                type_results[search_type] = results
                all_results.extend(results)
            
            # 3. 合并和排序结果
            if len(search_types) > 1:
                # 多类型合并
                final_results = self.similarity_ranker.merge_multi_type_results(
                    type_results.get('articles', []),
                    type_results.get('cases', []),
                    top_k,
                    merge_strategy
                )
            else:
                # 单类型排序
                final_results = self.similarity_ranker.rank_single_type_results(all_results)[:top_k]
            
            # 4. 格式化结果
            formatted_results = []
            for result in final_results:
                formatted_result = self.result_formatter.format_single_document(result, include_content=False)
                if formatted_result:
                    formatted_results.append(formatted_result)
            
            # 5. 内容增强和过滤
            if include_content:
                # 先获取更多结果以补偿可能被过滤掉的短内容
                extended_top_k = min(top_k * 2, len(formatted_results))
                candidates = formatted_results[:extended_top_k]
                
                # 增强内容
                enriched_candidates = self.content_enricher.enrich_results_with_content(
                    candidates, True, min_content_length=20
                )
                
                # 如果过滤后数量不足，取前top_k个
                formatted_results = enriched_candidates[:top_k]
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search execution error: {e}")
            return []
    
    def _search_in_single_type(self, query_vector, data_type: str, top_k: int) -> List[Dict[str, Any]]:
        """
        在单一数据类型中执行搜索
        
        Args:
            query_vector: 查询向量
            data_type: 数据类型 ('articles' 或 'cases')
            top_k: 返回数量
            
        Returns:
            原始搜索结果列表
        """
        try:
            # 获取向量和元数据
            vectors = self.data_loader.get_vectors(data_type)
            metadata = self.data_loader.get_metadata(data_type)
            
            if vectors is None or metadata is None:
                logger.warning(f"No data available for type: {data_type}")
                return []
            
            # 计算相似度并获取top-k
            top_indices, top_similarities = self.vector_calculator.calculate_and_rank(
                query_vector, vectors, top_k
            )
            
            # 构建结果
            results = []
            for idx, similarity in zip(top_indices, top_similarities):
                if idx < len(metadata):
                    result = {
                        'metadata': metadata[idx],
                        'similarity': float(similarity),
                        'type': data_type,
                        'index': int(idx)
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching in {data_type}: {e}")
            return []
    
    def search_articles_only(self, query: str, top_k: int = 10, 
                           include_content: bool = False) -> List[Dict[str, Any]]:
        """
        只搜索法条
        
        Args:
            query: 查询文本
            top_k: 返回数量
            include_content: 是否包含完整内容
            
        Returns:
            法条搜索结果
        """
        return self.execute_search(query, top_k, include_content, ['articles'])
    
    def search_cases_only(self, query: str, top_k: int = 10, 
                         include_content: bool = False) -> List[Dict[str, Any]]:
        """
        只搜索案例
        
        Args:
            query: 查询文本
            top_k: 返回数量
            include_content: 是否包含完整内容
            
        Returns:
            案例搜索结果
        """
        return self.execute_search(query, top_k, include_content, ['cases'])
    
    def get_document_by_id(self, doc_id: str, include_content: bool = True) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档
        
        Args:
            doc_id: 文档ID
            include_content: 是否包含完整内容
            
        Returns:
            文档数据或None
        """
        if not self.ensure_loaded():
            return None
        
        try:
            # 在法条中搜索
            articles_metadata = self.data_loader.get_metadata('articles')
            if articles_metadata:
                for meta in articles_metadata:
                    if meta.get('id') == doc_id:
                        result = {
                            'metadata': meta,
                            'type': 'articles'
                        }
                        formatted_result = self.result_formatter.format_single_document(result, False)
                        
                        if include_content and formatted_result:
                            formatted_result = self.content_enricher.enrich_single_result(formatted_result)
                        
                        return formatted_result
            
            # 在案例中搜索
            cases_metadata = self.data_loader.get_metadata('cases')
            if cases_metadata:
                for meta in cases_metadata:
                    if meta.get('id') == doc_id or meta.get('case_id') == doc_id:
                        result = {
                            'metadata': meta,
                            'type': 'cases'
                        }
                        formatted_result = self.result_formatter.format_single_document(result, False)
                        
                        if include_content and formatted_result:
                            formatted_result = self.content_enricher.enrich_single_result(formatted_result)
                        
                        return formatted_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        获取搜索系统统计信息
        
        Returns:
            统计信息字典
        """
        try:
            data_loader_stats = self.data_loader.get_stats() if self.data_loader else {}
            
            stats = {
                'coordinator_ready': self.loaded,
                'total_documents': data_loader_stats.get('total_documents', 0),
                'articles_count': len(self.data_loader.get_metadata('articles') or []),
                'cases_count': len(self.data_loader.get_metadata('cases') or []),
                'model_loaded': data_loader_stats.get('model_loaded', False),
                'vectors_loaded': data_loader_stats.get('vectors_loaded', False),
                'memory_usage_mb': data_loader_stats.get('memory_usage_mb', 0),
                'cached_contents': data_loader_stats.get('cached_contents', 0)
            }
            
            # 添加组件统计
            stats.update({
                'vector_calculator_stats': self.vector_calculator.get_calculation_stats(),
                'content_enricher_stats': self.content_enricher.get_content_stats(),
                'available_ranking_strategies': self.similarity_ranker.get_available_strategies(),
                'supported_result_types': self.result_formatter.get_supported_types()
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康检查结果
        """
        checks = {
            'coordinator_loaded': self.loaded,
            'data_loader_available': self.data_loader is not None,
            'vector_calculator_ready': bool(self.vector_calculator),
            'similarity_ranker_ready': bool(self.similarity_ranker),
            'result_formatter_ready': bool(self.result_formatter),
            'content_enricher_ready': bool(self.content_enricher)
        }
        
        if self.data_loader:
            data_loader_health = self.data_loader.health_check()
            checks.update(data_loader_health.get('checks', {}))
        
        return {
            'healthy': all(checks.values()),
            'checks': checks,
            'summary': f"{sum(checks.values())}/{len(checks)} checks passed"
        }