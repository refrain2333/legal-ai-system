#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版评分服务 - 解决分数过高和关键词匹配问题
集成到现有检索系统中
"""

import numpy as np
import jieba
import jieba.analyse
from typing import List, Dict, Any, Tuple
import re
from collections import Counter
import logging

class EnhancedScoringService:
    """增强版评分服务 - 解决三大核心问题"""
    
    def __init__(self):
        """初始化增强评分服务"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化智能关键词提取器
        from .smart_keyword_extractor import get_smart_keyword_extractor
        self.keyword_extractor = get_smart_keyword_extractor()
        self.logger.info("智能关键词提取器初始化成功")
        
        # 分数校准参数
        self.score_calibration = {
            'baseline_threshold': 0.3,    # 基线阈值
            'high_threshold': 0.7,        # 高分阈值  
            'max_score': 0.95,            # 最高分数限制
            'noise_penalty': 0.3,         # 噪声词惩罚
            'length_penalty_threshold': 6  # 长度惩罚阈值
        }
        
        # 动态权重配置
        self.weight_profiles = {
            'semantic_focused': {'semantic': 0.8, 'keyword': 0.15, 'type': 0.05},
            'keyword_focused': {'semantic': 0.6, 'keyword': 0.3, 'type': 0.1},
            'balanced': {'semantic': 0.7, 'keyword': 0.2, 'type': 0.1}
        }
    
    def calibrate_semantic_score(self, raw_score: float, 
                                query: str, document: Dict[str, Any]) -> float:
        """
        语义分数校准 - 核心功能
        
        解决问题1: 默认分数过高
        """
        
        # 1. 基础分数映射：将0.5-1.0的集中区间重新分布到0.1-0.9
        config = self.score_calibration
        
        if raw_score < config['baseline_threshold']:
            # 低分区间：保持较低分数
            calibrated = raw_score * 0.3
            
        elif raw_score < config['high_threshold']:
            # 中分区间：线性映射到0.1-0.4
            range_input = raw_score - config['baseline_threshold']
            range_size = config['high_threshold'] - config['baseline_threshold']
            calibrated = 0.1 + (range_input / range_size) * 0.3
            
        else:
            # 高分区间：映射到0.4-0.9，保持区分度
            range_input = raw_score - config['high_threshold']
            range_size = 1.0 - config['high_threshold']
            calibrated = 0.4 + (range_input / range_size) * 0.5
        
        # 2. 查询质量惩罚
        penalty_factor = 1.0
        
        # 过短查询惩罚
        if len(query) < config['length_penalty_threshold']:
            penalty_factor *= 0.8
            
        # 噪声词检测
        noise_words = {'随机', '无关', '测试', '无意义', '垃圾', '乱码'}
        if any(word in query for word in noise_words):
            penalty_factor *= config['noise_penalty']
        
        # 重复词惩罚 - 使用智能分词
        try:
            words = [kw[0] for kw in self.keyword_extractor.extract_keywords_multi_algorithm(query, 10)]
        except:
            words = query.split()  # 备用方案
            
        if len(words) != len(set(words)):  # 有重复词
            penalty_factor *= 0.9
        
        # 3. 应用惩罚并限制最高分
        final_score = calibrated * penalty_factor
        return min(final_score, config['max_score'])
    
    def extract_enhanced_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        增强版关键词提取 - 使用智能多算法提取器
        
        解决问题2: 关键词列表有限且粗糙
        """
        
        try:
            # 使用智能关键词提取器
            return self.keyword_extractor.extract_keywords_multi_algorithm(text, top_k)
            
        except Exception as e:
            self.logger.error(f"智能关键词提取失败: {e}")
            # 备用方案：简单分词
            return self._fallback_keyword_extraction(text, top_k)
    
    def _fallback_keyword_extraction(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """备用关键词提取方案"""
        # 简单的中文词汇提取
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        
        # 词频统计
        word_counter = Counter(chinese_words)
        
        # 转换为权重格式
        total_count = sum(word_counter.values()) or 1
        keywords_with_weights = [
            (word, count / total_count) 
            for word, count in word_counter.most_common(top_k)
        ]
        
        return keywords_with_weights
    
    def compute_keyword_similarity(self, query: str, document: Dict[str, Any]) -> float:
        """
        计算关键词相似度 - 使用智能提取器
        
        解决问题3: 匹配逻辑过于简单
        """
        
        try:
            # 使用智能关键词提取器计算相似度
            doc_text = (document.get('title', '') + ' ' + 
                       document.get('content_preview', '')[:1000])
            
            return self.keyword_extractor.compute_keyword_similarity(query, doc_text)
            
        except Exception as e:
            self.logger.error(f"智能相似度计算失败: {e}")
            return self._fallback_similarity_computation(query, document)
    
    def _fallback_similarity_computation(self, query: str, document: Dict[str, Any]) -> float:
        """备用相似度计算方案"""
        query_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', query))
        doc_text = document.get('title', '') + ' ' + document.get('content_preview', '')[:500]
        doc_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', doc_text))
        
        if not query_words or not doc_words:
            return 0.0
        
        # 简单的Jaccard相似度
        intersection = len(query_words & doc_words)
        union = len(query_words | doc_words)
        
        return intersection / union if union > 0 else 0.0
    
    def compute_enhanced_final_score(self, query: str, document: Dict[str, Any], 
                                   base_semantic_score: float) -> Dict[str, Any]:
        """
        计算最终增强分数
        
        综合解决三个核心问题
        """
        
        # 1. 校准语义分数
        calibrated_semantic = self.calibrate_semantic_score(
            base_semantic_score, query, document
        )
        
        # 2. 计算关键词匹配分数
        keyword_score = self.compute_keyword_similarity(query, document)
        
        # 3. 计算文档类型匹配分数
        type_score = self._compute_type_relevance(query, document)
        
        # 4. 选择权重配置
        weight_profile = self._select_weight_profile(query, keyword_score)
        weights = self.weight_profiles[weight_profile]
        
        # 5. 计算加权最终分数
        final_score = (
            weights['semantic'] * calibrated_semantic +
            weights['keyword'] * keyword_score +
            weights['type'] * type_score
        )
        
        # 6. 应用最终校准
        final_score = min(final_score, self.score_calibration['max_score'])
        
        return {
            'final_score': final_score,
            'component_scores': {
                'original_semantic': base_semantic_score,
                'calibrated_semantic': calibrated_semantic,
                'keyword_similarity': keyword_score,
                'type_relevance': type_score
            },
            'weights_used': weights,
            'weight_profile': weight_profile
        }
    
    def _compute_type_relevance(self, query: str, document: Dict[str, Any]) -> float:
        """计算文档类型相关性"""
        doc_type = document.get('type', '').lower()
        
        # 类型提示词识别
        law_indicators = ['法条', '法律', '条文', '规定', '办法', '条例']
        case_indicators = ['案例', '判决', '裁判', '审理', '当事人', '法院']
        
        query_lower = query.lower()
        
        if doc_type == 'law':
            if any(indicator in query_lower for indicator in law_indicators):
                return 0.8
            elif any(indicator in query_lower for indicator in case_indicators):
                return 0.3  # 用户要案例但给了法条
            else:
                return 0.5  # 中性
                
        elif doc_type == 'case':
            if any(indicator in query_lower for indicator in case_indicators):
                return 0.8
            elif any(indicator in query_lower for indicator in law_indicators):
                return 0.3  # 用户要法条但给了案例
            else:
                return 0.5  # 中性
        
        return 0.5  # 未知类型
    
    def _select_weight_profile(self, query: str, keyword_score: float) -> str:
        """动态选择权重配置"""
        
        if len(query) <= 4:
            # 短查询更依赖关键词匹配
            return 'keyword_focused'
        elif keyword_score > 0.6:
            # 关键词匹配很好时使用平衡权重
            return 'balanced'
        elif keyword_score < 0.2:
            # 关键词匹配差时更依赖语义
            return 'semantic_focused'
        else:
            # 默认平衡
            return 'balanced'

# 全局实例
_enhanced_scoring_service = None

def get_enhanced_scoring_service() -> EnhancedScoringService:
    """获取全局增强评分服务实例"""
    global _enhanced_scoring_service
    if _enhanced_scoring_service is None:
        _enhanced_scoring_service = EnhancedScoringService()
    return _enhanced_scoring_service