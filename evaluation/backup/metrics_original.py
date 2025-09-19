#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估指标计算模块
实现各种信息检索评估指标
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """评估指标计算器"""
    
    def __init__(self):
        """初始化指标计算器"""
        self.metrics_history = []
    
    def precision_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        计算Precision@K
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            k: 截断位置
            
        Returns:
            Precision@K值
        """
        if k <= 0 or not retrieved:
            return 0.0
        
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        
        relevant_in_k = sum(1 for doc in retrieved_k if doc in relevant_set)
        return relevant_in_k / len(retrieved_k)
    
    def recall_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        计算Recall@K
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            k: 截断位置
            
        Returns:
            Recall@K值
        """
        if not relevant:
            return 0.0
        
        if k <= 0 or not retrieved:
            return 0.0
        
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        
        relevant_in_k = sum(1 for doc in retrieved_k if doc in relevant_set)
        return relevant_in_k / len(relevant_set)
    
    def f1_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        计算F1@K
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            k: 截断位置
            
        Returns:
            F1@K值
        """
        precision = self.precision_at_k(retrieved, relevant, k)
        recall = self.recall_at_k(retrieved, relevant, k)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def average_precision(self, retrieved: List[str], relevant: List[str]) -> float:
        """
        计算Average Precision (AP)
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            
        Returns:
            AP值
        """
        if not relevant:
            return 0.0
        
        relevant_set = set(relevant)
        ap_sum = 0.0
        relevant_found = 0
        
        for i, doc in enumerate(retrieved):
            if doc in relevant_set:
                relevant_found += 1
                precision_at_i = relevant_found / (i + 1)
                ap_sum += precision_at_i
        
        if relevant_found == 0:
            return 0.0
        
        return ap_sum / len(relevant_set)
    
    def mean_average_precision(self, results: List[Dict[str, Any]]) -> float:
        """
        计算Mean Average Precision (MAP)
        
        Args:
            results: 包含retrieved和relevant的结果列表
            
        Returns:
            MAP值
        """
        if not results:
            return 0.0
        
        ap_scores = []
        for result in results:
            ap = self.average_precision(
                result.get('retrieved', []),
                result.get('relevant', [])
            )
            ap_scores.append(ap)
        
        return np.mean(ap_scores) if ap_scores else 0.0
    
    def dcg_at_k(self, scores: List[float], k: int) -> float:
        """
        计算Discounted Cumulative Gain@K
        
        Args:
            scores: 相关性得分列表
            k: 截断位置
            
        Returns:
            DCG@K值
        """
        if k <= 0 or not scores:
            return 0.0
        
        scores_k = scores[:k]
        discounts = np.log2(np.arange(2, len(scores_k) + 2))
        return np.sum(np.array(scores_k) / discounts)
    
    def ndcg_at_k(self, retrieved: List[str], relevant: List[str], 
                  relevance_scores: Dict[str, float], k: int) -> float:
        """
        计算Normalized DCG@K
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            relevance_scores: 文档相关性得分字典
            k: 截断位置
            
        Returns:
            NDCG@K值
        """
        if k <= 0 or not retrieved:
            return 0.0
        
        # 获取检索结果的相关性得分
        retrieved_scores = [
            relevance_scores.get(doc, 0.0) for doc in retrieved[:k]
        ]
        
        # 计算DCG
        dcg = self.dcg_at_k(retrieved_scores, k)
        
        # 计算理想的DCG (IDCG)
        ideal_scores = sorted([
            relevance_scores.get(doc, 0.0) for doc in relevant
        ], reverse=True)[:k]
        
        idcg = self.dcg_at_k(ideal_scores, k)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def reciprocal_rank(self, retrieved: List[str], relevant: List[str]) -> float:
        """
        计算Reciprocal Rank
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            
        Returns:
            RR值
        """
        relevant_set = set(relevant)
        
        for i, doc in enumerate(retrieved):
            if doc in relevant_set:
                return 1.0 / (i + 1)
        
        return 0.0
    
    def mean_reciprocal_rank(self, results: List[Dict[str, Any]]) -> float:
        """
        计算Mean Reciprocal Rank (MRR)
        
        Args:
            results: 包含retrieved和relevant的结果列表
            
        Returns:
            MRR值
        """
        if not results:
            return 0.0
        
        rr_scores = []
        for result in results:
            rr = self.reciprocal_rank(
                result.get('retrieved', []),
                result.get('relevant', [])
            )
            rr_scores.append(rr)
        
        return np.mean(rr_scores) if rr_scores else 0.0
    
    def calculate_all_metrics(self, retrieved: List[str], relevant: List[str],
                             k_values: List[int] = None,
                             relevance_scores: Dict[str, float] = None) -> Dict[str, Any]:
        """
        计算所有评估指标
        
        Args:
            retrieved: 检索到的文档ID列表
            relevant: 相关文档ID列表
            k_values: K值列表
            relevance_scores: 文档相关性得分字典
            
        Returns:
            包含所有指标的字典
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]
        
        metrics = {}
        
        # 计算不同K值的指标
        for k in k_values:
            metrics[f'precision@{k}'] = self.precision_at_k(retrieved, relevant, k)
            metrics[f'recall@{k}'] = self.recall_at_k(retrieved, relevant, k)
            metrics[f'f1@{k}'] = self.f1_at_k(retrieved, relevant, k)
            
            if relevance_scores:
                metrics[f'ndcg@{k}'] = self.ndcg_at_k(
                    retrieved, relevant, relevance_scores, k
                )
        
        # 计算其他指标
        metrics['average_precision'] = self.average_precision(retrieved, relevant)
        metrics['reciprocal_rank'] = self.reciprocal_rank(retrieved, relevant)
        
        return metrics
    
    def aggregate_metrics(self, all_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合多个查询的指标
        
        Args:
            all_metrics: 所有查询的指标列表
            
        Returns:
            聚合后的指标字典
        """
        if not all_metrics:
            return {}
        
        aggregated = defaultdict(list)
        
        # 收集所有指标值
        for metrics in all_metrics:
            for key, value in metrics.items():
                aggregated[key].append(value)
        
        # 计算均值和标准差
        result = {}
        for key, values in aggregated.items():
            result[f'{key}_mean'] = np.mean(values)
            result[f'{key}_std'] = np.std(values)
            result[f'{key}_min'] = np.min(values)
            result[f'{key}_max'] = np.max(values)
        
        return result


class SemanticMetrics:
    """语义相关性评估指标"""
    
    def __init__(self):
        """初始化语义指标计算器"""
        self.results_cache = {}
    
    def article_case_accuracy(self, search_results: List[Dict], 
                             ground_truth: Dict[int, List[str]]) -> float:
        """
        计算法条-案例关联准确率
        
        Args:
            search_results: 搜索结果列表
            ground_truth: 真实的法条-案例映射
            
        Returns:
            准确率
        """
        if not search_results:
            return 0.0
        
        correct = 0
        total = 0
        
        for result in search_results:
            article_num = result.get('article_number')
            retrieved_cases = result.get('retrieved_cases', [])
            
            if article_num in ground_truth:
                true_cases = set(ground_truth[article_num])
                retrieved_set = set(retrieved_cases)
                
                if true_cases.intersection(retrieved_set):
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0.0
    
    def case_article_accuracy(self, search_results: List[Dict],
                             case_article_mapping: Dict[str, List[int]]) -> float:
        """
        计算案例-法条关联准确率
        
        Args:
            search_results: 搜索结果列表
            case_article_mapping: 案例到法条的映射
            
        Returns:
            准确率
        """
        if not search_results:
            return 0.0
        
        correct = 0
        total = 0
        
        for result in search_results:
            case_id = result.get('case_id')
            retrieved_articles = result.get('retrieved_articles', [])
            
            if case_id in case_article_mapping:
                true_articles = set(case_article_mapping[case_id])
                retrieved_set = set(retrieved_articles)
                
                if true_articles.intersection(retrieved_set):
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0.0
    
    def crime_keyword_accuracy(self, search_results: List[Dict]) -> float:
        """
        计算罪名关键词搜索准确率
        
        Args:
            search_results: 搜索结果列表
            
        Returns:
            准确率
        """
        if not search_results:
            return 0.0
        
        correct = 0
        total = len(search_results)

        for result in search_results:
            query_crime = result.get('query_crime')
            retrieved_crimes = result.get('retrieved_crimes', [])

            # 检查查询的罪名是否在检索结果中
            if query_crime in retrieved_crimes:
                correct += 1

        return correct / total if total > 0 else 0.0

    def crime_consistency_metrics(self, search_result: Dict) -> Dict[str, float]:
        """
        计算罪名一致性评估指标

        Args:
            search_result: 混合搜索结果，包含articles和cases

        Returns:
            一致性指标字典
        """
        if not isinstance(search_result, dict):
            return {'precision': 0.0, 'recall': 0.0, 'jaccard': 0.0}

        articles = search_result.get('articles', [])
        cases = search_result.get('cases', [])

        # 提取返回的法条编号
        returned_articles = set()
        for article in articles:
            article_num = article.get('article_number')
            if article_num:
                returned_articles.add(article_num)

        # 提取案例引用的法条编号
        case_cited_articles = set()
        for case in cases:
            relevant_articles = case.get('relevant_articles', [])
            if relevant_articles:
                case_cited_articles.update(relevant_articles)

        # 计算交集
        intersection = returned_articles.intersection(case_cited_articles)

        # 计算指标
        precision = len(intersection) / len(returned_articles) if returned_articles else 0.0
        recall = len(intersection) / len(case_cited_articles) if case_cited_articles else 0.0

        # Jaccard相似系数
        union = returned_articles.union(case_cited_articles)
        jaccard = len(intersection) / len(union) if union else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'jaccard': jaccard,
            'returned_articles_count': len(returned_articles),
            'case_cited_articles_count': len(case_cited_articles),
            'intersection_count': len(intersection)
        }