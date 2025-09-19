#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相似度排序器
负责结果排序和合并逻辑
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class SimilarityRanker:
    """相似度排序器 - 专注于排序逻辑"""
    
    def __init__(self):
        """初始化排序器"""
        self.sort_strategies = {
            'similarity_desc': self._sort_by_similarity_desc,
            'similarity_asc': self._sort_by_similarity_asc,
            'type_then_similarity': self._sort_by_type_then_similarity,
            'balanced_mix': self._balanced_type_mix
        }
    
    def rank_single_type_results(self, results: List[Dict[str, Any]], 
                                sort_strategy: str = 'similarity_desc') -> List[Dict[str, Any]]:
        """
        对单一类型的搜索结果进行排序
        
        Args:
            results: 搜索结果列表
            sort_strategy: 排序策略
            
        Returns:
            排序后的结果列表
        """
        if not results:
            return []
        
        strategy_func = self.sort_strategies.get(sort_strategy, self._sort_by_similarity_desc)
        return strategy_func(results)
    
    def merge_multi_type_results(self, articles_results: List[Dict[str, Any]], 
                               cases_results: List[Dict[str, Any]], 
                               total_top_k: int,
                               merge_strategy: str = 'interleaved') -> List[Dict[str, Any]]:
        """
        合并多种类型的搜索结果
        
        Args:
            articles_results: 法条搜索结果
            cases_results: 案例搜索结果  
            total_top_k: 最终返回数量
            merge_strategy: 合并策略
            
        Returns:
            合并后的top-k结果
        """
        if merge_strategy == 'interleaved':
            return self._interleaved_merge(articles_results, cases_results, total_top_k)
        elif merge_strategy == 'similarity_priority':
            return self._similarity_priority_merge(articles_results, cases_results, total_top_k)
        elif merge_strategy == 'balanced_mix':
            return self._balanced_mix_merge(articles_results, cases_results, total_top_k)
        else:
            # 默认：合并后按相似度排序
            return self._simple_merge(articles_results, cases_results, total_top_k)
    
    def _sort_by_similarity_desc(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按相似度降序排序"""
        return sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
    
    def _sort_by_similarity_asc(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按相似度升序排序"""
        return sorted(results, key=lambda x: x.get('similarity', 0), reverse=False)
    
    def _sort_by_type_then_similarity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """先按类型分组，再按相似度排序"""
        # 法条优先，然后案例
        articles = [r for r in results if r.get('type') == 'articles']
        cases = [r for r in results if r.get('type') == 'cases']
        
        articles_sorted = self._sort_by_similarity_desc(articles)
        cases_sorted = self._sort_by_similarity_desc(cases)
        
        return articles_sorted + cases_sorted
    
    def _balanced_type_mix(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """平衡类型混合排序"""
        return self._sort_by_similarity_desc(results)  # 基础实现
    
    def _simple_merge(self, articles_results: List[Dict[str, Any]], 
                     cases_results: List[Dict[str, Any]], 
                     total_top_k: int) -> List[Dict[str, Any]]:
        """简单合并：合并所有结果后按相似度排序"""
        all_results = articles_results + cases_results
        sorted_results = self._sort_by_similarity_desc(all_results)
        return sorted_results[:total_top_k]
    
    def _interleaved_merge(self, articles_results: List[Dict[str, Any]], 
                          cases_results: List[Dict[str, Any]], 
                          total_top_k: int) -> List[Dict[str, Any]]:
        """交错合并：法条和案例轮流选择"""
        result = []
        a_idx, c_idx = 0, 0
        
        # 先按相似度排序各自的结果
        articles_sorted = self._sort_by_similarity_desc(articles_results)
        cases_sorted = self._sort_by_similarity_desc(cases_results)
        
        # 交错选择
        while len(result) < total_top_k and (a_idx < len(articles_sorted) or c_idx < len(cases_sorted)):
            # 根据相似度决定优先选择哪个类型
            article_sim = articles_sorted[a_idx].get('similarity', 0) if a_idx < len(articles_sorted) else 0
            case_sim = cases_sorted[c_idx].get('similarity', 0) if c_idx < len(cases_sorted) else 0
            
            if article_sim >= case_sim and a_idx < len(articles_sorted):
                result.append(articles_sorted[a_idx])
                a_idx += 1
            elif c_idx < len(cases_sorted):
                result.append(cases_sorted[c_idx])
                c_idx += 1
            else:
                break
        
        return result
    
    def _similarity_priority_merge(self, articles_results: List[Dict[str, Any]], 
                                 cases_results: List[Dict[str, Any]], 
                                 total_top_k: int) -> List[Dict[str, Any]]:
        """完全按相似度优先合并"""
        return self._simple_merge(articles_results, cases_results, total_top_k)
    
    def _balanced_mix_merge(self, articles_results: List[Dict[str, Any]], 
                          cases_results: List[Dict[str, Any]], 
                          total_top_k: int) -> List[Dict[str, Any]]:
        """平衡混合：确保两种类型都有代表"""
        # 确保至少有30%的结果来自每种类型（如果该类型有结果）
        min_each_type = max(1, total_top_k // 3)
        
        articles_sorted = self._sort_by_similarity_desc(articles_results)
        cases_sorted = self._sort_by_similarity_desc(cases_results)
        
        # 先从每种类型选择最高相似度的结果
        selected_articles = articles_sorted[:min_each_type] if articles_sorted else []
        selected_cases = cases_sorted[:min_each_type] if cases_sorted else []
        
        result = selected_articles + selected_cases
        
        # 剩余位置按相似度填充
        remaining_spots = total_top_k - len(result)
        if remaining_spots > 0:
            remaining_articles = articles_sorted[len(selected_articles):]
            remaining_cases = cases_sorted[len(selected_cases):]
            
            all_remaining = remaining_articles + remaining_cases
            remaining_sorted = self._sort_by_similarity_desc(all_remaining)
            
            result.extend(remaining_sorted[:remaining_spots])
        
        # 最终按相似度排序
        return self._sort_by_similarity_desc(result)
    
    def calculate_ranking_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算排序质量指标
        
        Args:
            results: 排序后的结果
            
        Returns:
            排序质量指标
        """
        if not results:
            return {'total_results': 0}
        
        similarities = [r.get('similarity', 0) for r in results]
        types = [r.get('type', 'unknown') for r in results]
        
        return {
            'total_results': len(results),
            'avg_similarity': np.mean(similarities) if similarities else 0,
            'min_similarity': min(similarities) if similarities else 0,
            'max_similarity': max(similarities) if similarities else 0,
            'similarity_std': np.std(similarities) if similarities else 0,
            'type_distribution': {t: types.count(t) for t in set(types)},
            'similarity_range': max(similarities) - min(similarities) if similarities else 0,
            'is_descending_sorted': self._is_descending_sorted(similarities)
        }
    
    def _is_descending_sorted(self, similarities: List[float]) -> bool:
        """检查相似度是否按降序排列"""
        if len(similarities) <= 1:
            return True
        
        for i in range(1, len(similarities)):
            if similarities[i-1] < similarities[i]:
                return False
        return True
    
    def get_available_strategies(self) -> Dict[str, str]:
        """
        获取可用的排序策略
        
        Returns:
            策略名称和描述的映射
        """
        return {
            'similarity_desc': '按相似度降序排序',
            'similarity_asc': '按相似度升序排序', 
            'type_then_similarity': '先按类型分组，再按相似度排序',
            'balanced_mix': '平衡类型混合排序'
        }