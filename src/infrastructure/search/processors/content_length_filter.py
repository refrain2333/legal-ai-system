#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容长度过滤器
专门用于过滤内容过短的文档
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContentLengthFilter:
    """内容长度过滤器 - 过滤内容过短的文档"""
    
    def __init__(self, min_content_length: int = 20):
        """
        初始化过滤器
        
        Args:
            min_content_length: 最小内容长度阈值
        """
        self.min_content_length = min_content_length
    
    def filter_by_metadata_length(self, results: List[Dict[str, Any]], data_loader) -> List[Dict[str, Any]]:
        """
        基于元数据中的内容长度信息进行快速过滤
        
        Args:
            results: 搜索结果列表
            data_loader: 数据加载器，用于获取内容长度信息
            
        Returns:
            过滤后的结果列表
        """
        filtered_results = []
        filtered_count = 0
        
        for result in results:
            # 尝试从元数据获取内容长度
            content_length = self._get_content_length_from_metadata(result, data_loader)
            
            if content_length is not None and content_length >= self.min_content_length:
                filtered_results.append(result)
            elif content_length is not None and content_length < self.min_content_length:
                filtered_count += 1
                logger.debug(f"Filtered document {result.get('id', 'unknown')} by metadata: {content_length} characters")
            else:
                # 如果无法从元数据判断，暂时保留，交给后续步骤处理
                filtered_results.append(result)
        
        if filtered_count > 0:
            logger.info(f"Pre-filtered {filtered_count} documents by metadata content length")
        
        return filtered_results
    
    def filter_by_actual_content(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于实际加载的内容进行过滤
        
        Args:
            results: 已加载内容的结果列表
            
        Returns:
            过滤后的结果列表
        """
        filtered_results = []
        filtered_count = 0
        
        for result in results:
            content = result.get('content', '')
            content_length = len(content.strip()) if content else 0
            
            if content_length >= self.min_content_length:
                filtered_results.append(result)
            else:
                filtered_count += 1
                logger.debug(f"Filtered document {result.get('id', 'unknown')} by actual content: {content_length} characters")
        
        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count} documents by actual content length")
        
        return filtered_results
    
    def _get_content_length_from_metadata(self, result: Dict[str, Any], data_loader) -> int:
        """
        从元数据中获取内容长度信息
        
        Args:
            result: 搜索结果
            data_loader: 数据加载器
            
        Returns:
            内容长度，如果无法获取则返回None
        """
        try:
            # 尝试从结果的metadata获取
            metadata = result.get('metadata', result)
            
            # 检查是否有预存的内容长度字段
            if 'content_length' in metadata:
                return metadata['content_length']
            
            # 对于法条，可以尝试快速估算
            if result.get('type') in ['article', 'articles']:
                # 法条通常有标准的长度范围，可以基于article_number等信息估算
                # 这里简化处理，返回None让后续流程处理
                return None
            
            # 对于案例，检查是否有fact字段的长度信息
            elif result.get('type') in ['case', 'cases']:
                # 同样简化处理
                return None
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting content length from metadata: {e}")
            return None
    
    def apply_intelligent_filtering(self, results: List[Dict[str, Any]], 
                                  data_loader, target_count: int) -> List[Dict[str, Any]]:
        """
        智能过滤：根据目标数量和内容质量进行过滤
        
        Args:
            results: 搜索结果列表
            data_loader: 数据加载器
            target_count: 目标返回数量
            
        Returns:
            过滤后的结果列表
        """
        # 1. 先进行元数据快速过滤
        pre_filtered = self.filter_by_metadata_length(results, data_loader)
        
        # 2. 如果过滤后数量仍然充足，直接返回
        if len(pre_filtered) >= target_count * 1.5:  # 保留一些余量
            return pre_filtered[:target_count * 2]  # 返回目标数量的2倍，供后续选择
        
        # 3. 如果数量不足，返回更多结果供后续内容过滤
        return pre_filtered
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """
        获取过滤器统计信息
        
        Returns:
            过滤器配置和统计信息
        """
        return {
            'min_content_length': self.min_content_length,
            'filter_enabled': True,
            'filter_strategy': 'content_length_based'
        }