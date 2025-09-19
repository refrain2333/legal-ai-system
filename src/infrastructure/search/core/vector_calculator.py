#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量计算核心模块
负责查询编码和相似度计算
"""

import numpy as np
from typing import Optional, Tuple, List
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class VectorCalculator:
    """核心向量计算器 - 高内聚的计算逻辑"""
    
    def __init__(self, data_loader):
        """
        初始化向量计算器
        
        Args:
            data_loader: 数据加载器实例
        """
        self.data_loader = data_loader
    
    def encode_query(self, query: str) -> Optional[np.ndarray]:
        """
        编码查询文本为向量
        
        Args:
            query: 查询文本
            
        Returns:
            查询向量，失败返回None
        """
        try:
            return self.data_loader.encode_query(query)
        except Exception as e:
            logger.error(f"Query encoding failed: {e}")
            return None
    
    def calculate_similarities(self, query_vector: np.ndarray, 
                             document_vectors: np.ndarray) -> np.ndarray:
        """
        计算查询向量与文档向量的相似度
        
        Args:
            query_vector: 查询向量 (1, 768)
            document_vectors: 文档向量矩阵 (N, 768)
            
        Returns:
            相似度数组 (N,)
        """
        try:
            similarities = cosine_similarity(query_vector, document_vectors)[0]
            return similarities
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return np.array([])
    
    def get_top_k_indices(self, similarities: np.ndarray, top_k: int) -> np.ndarray:
        """
        获取top-k相似度的索引
        
        Args:
            similarities: 相似度数组
            top_k: 返回数量
            
        Returns:
            top-k索引数组，按相似度降序排列
        """
        if len(similarities) == 0:
            return np.array([], dtype=int)
        
        # 使用argpartition进行高效的top-k选择
        if top_k >= len(similarities):
            # 如果要求的数量大于等于总数，直接排序全部
            return np.argsort(similarities)[::-1]
        else:
            # 使用argpartition + argsort的混合策略提高性能
            top_k_unsorted = np.argpartition(similarities, -top_k)[-top_k:]
            # 对top-k结果进行排序
            sorted_indices = np.argsort(similarities[top_k_unsorted])[::-1]
            return top_k_unsorted[sorted_indices]
    
    def calculate_and_rank(self, query_vector: np.ndarray, 
                          document_vectors: np.ndarray, 
                          top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        一站式计算相似度并返回top-k结果
        
        Args:
            query_vector: 查询向量
            document_vectors: 文档向量矩阵
            top_k: 返回数量
            
        Returns:
            (top_k_indices, top_k_similarities)
        """
        similarities = self.calculate_similarities(query_vector, document_vectors)
        
        if len(similarities) == 0:
            return np.array([], dtype=int), np.array([])
        
        top_indices = self.get_top_k_indices(similarities, top_k)
        top_similarities = similarities[top_indices]
        
        return top_indices, top_similarities
    
    def batch_calculate_similarities(self, query_vectors: np.ndarray, 
                                   document_vectors: np.ndarray) -> np.ndarray:
        """
        批量计算多个查询的相似度
        
        Args:
            query_vectors: 查询向量矩阵 (M, 768)
            document_vectors: 文档向量矩阵 (N, 768)
            
        Returns:
            相似度矩阵 (M, N)
        """
        try:
            return cosine_similarity(query_vectors, document_vectors)
        except Exception as e:
            logger.error(f"Batch similarity calculation failed: {e}")
            return np.array([])
    
    def validate_vector_dimensions(self, vector: np.ndarray, 
                                 expected_dim: int = 768) -> bool:
        """
        验证向量维度
        
        Args:
            vector: 待验证向量
            expected_dim: 期望维度
            
        Returns:
            是否符合期望维度
        """
        if vector is None:
            return False
        
        if vector.ndim == 1:
            return vector.shape[0] == expected_dim
        elif vector.ndim == 2:
            return vector.shape[1] == expected_dim
        else:
            return False
    
    def get_calculation_stats(self) -> dict:
        """
        获取计算统计信息
        
        Returns:
            计算器统计信息
        """
        return {
            'calculator_ready': self.data_loader is not None,
            'model_loaded': self.data_loader.model_loaded if self.data_loader else False,
            'supported_similarity_metrics': ['cosine'],
            'expected_vector_dimension': 768
        }