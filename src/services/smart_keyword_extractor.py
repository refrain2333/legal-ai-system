#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能关键词提取服务 - 取代硬编码词典
集成多种算法：TF-IDF + TextRank + KeyBERT + 动态词典
"""

import numpy as np
import jieba
import jieba.analyse
from typing import List, Dict, Any, Tuple
import pickle
import re
from pathlib import Path
import logging
from collections import Counter

class SmartKeywordExtractor:
    """智能关键词提取器 - 动态学习法律词汇"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化jieba
        self._init_jieba()
        
        # 加载动态法律词典
        self.dynamic_legal_dict = self._load_dynamic_legal_dictionary()
        
        # KeyBERT模型 (延迟加载)
        self.keybert_model = None
        
        # 提取算法权重
        self.algorithm_weights = {
            'tfidf': 0.4,       # TF-IDF权重
            'textrank': 0.3,    # TextRank权重  
            'keybert': 0.2,     # KeyBERT语义权重
            'frequency': 0.1    # 词频权重
        }
        
        # 缓存机制
        self.keyword_cache = {}
        self.max_cache_size = 1000
        
    def _init_jieba(self):
        """初始化jieba分词器"""
        try:
            jieba.initialize()
            self.jieba_available = True
            self.logger.info("jieba分词器初始化成功")
        except Exception as e:
            self.logger.warning(f"jieba初始化失败: {e}")
            self.jieba_available = False
    
    def _load_dynamic_legal_dictionary(self) -> Dict[str, Any]:
        """加载动态生成的法律词典"""
        dict_path = Path('data/processed/dynamic_legal_dictionary.pkl')
        
        try:
            if dict_path.exists():
                with open(dict_path, 'rb') as f:
                    dynamic_dict = pickle.load(f)
                
                total_words = len(dynamic_dict.get('all_keywords', {}))
                self.logger.info(f"加载动态法律词典: {total_words} 个专业词汇")
                
                # 将高权重词汇加入jieba词典
                if self.jieba_available:
                    high_weight_words = dynamic_dict.get('high_weight', {})
                    for word, weight in high_weight_words.items():
                        jieba.add_word(word, freq=int(weight * 10000), tag='legal_high')
                
                return dynamic_dict
            else:
                self.logger.warning("动态法律词典不存在，使用默认配置")
                return self._get_fallback_dictionary()
                
        except Exception as e:
            self.logger.error(f"动态词典加载失败: {e}")
            return self._get_fallback_dictionary()
    
    def _get_fallback_dictionary(self) -> Dict[str, Any]:
        """备用法律词典"""
        fallback_words = {
            # 核心法律词汇
            '合同': 0.05, '违约': 0.04, '责任': 0.045, '赔偿': 0.04,
            '诉讼': 0.04, '法院': 0.035, '判决': 0.035, '证据': 0.03,
            '当事人': 0.03, '权利': 0.035, '义务': 0.035, '损害': 0.03,
            '刑法': 0.03, '民法': 0.03, '行政': 0.025, '程序': 0.025
        }
        
        return {
            'all_keywords': fallback_words,
            'high_weight': {k: v for k, v in fallback_words.items() if v > 0.035},
            'legal_pattern': {k: v for k, v in fallback_words.items() if v <= 0.035},
            'medium_weight': {}
        }
    
    def _init_keybert(self):
        """延迟初始化KeyBERT模型"""
        if self.keybert_model is None:
            try:
                # 尝试使用已有的语义模型
                from ..models.semantic_embedding import SemanticTextEmbedding
                embedding_model = SemanticTextEmbedding()
                
                # 简化版语义关键词提取
                self.keybert_model = embedding_model
                self.logger.info("KeyBERT语义提取器初始化成功")
                
            except Exception as e:
                self.logger.warning(f"KeyBERT初始化失败，跳过语义提取: {e}")
                self.keybert_model = False  # 标记为不可用
    
    def extract_keywords_multi_algorithm(self, text: str, top_k: int = 15) -> List[Tuple[str, float]]:
        """
        多算法融合关键词提取
        
        Args:
            text: 输入文本
            top_k: 返回关键词数量
            
        Returns:
            List[Tuple[str, float]]: [(关键词, 权重分数), ...]
        """
        
        if not text or len(text.strip()) < 5:
            return []
        
        # 检查缓存
        cache_key = hash(text[:200])  # 使用前200字符作为缓存键
        if cache_key in self.keyword_cache:
            cached_result = self.keyword_cache[cache_key]
            return cached_result[:top_k]
        
        # 多算法提取结果汇总
        all_keywords = {}
        
        # 1. TF-IDF算法
        tfidf_keywords = self._extract_tfidf_keywords(text, top_k * 2)
        for word, weight in tfidf_keywords:
            all_keywords[word] = all_keywords.get(word, 0) + weight * self.algorithm_weights['tfidf']
        
        # 2. TextRank算法
        textrank_keywords = self._extract_textrank_keywords(text, top_k * 2)
        for word, weight in textrank_keywords:
            all_keywords[word] = all_keywords.get(word, 0) + weight * self.algorithm_weights['textrank']
        
        # 3. 词频统计 (备用)
        freq_keywords = self._extract_frequency_keywords(text, top_k)
        for word, weight in freq_keywords:
            all_keywords[word] = all_keywords.get(word, 0) + weight * self.algorithm_weights['frequency']
        
        # 4. KeyBERT语义提取 (如果可用)
        if self.keybert_model is None:
            self._init_keybert()
        
        if self.keybert_model and self.keybert_model is not False:
            semantic_keywords = self._extract_semantic_keywords(text, top_k)
            for word, weight in semantic_keywords:
                all_keywords[word] = all_keywords.get(word, 0) + weight * self.algorithm_weights['keybert']
        
        # 5. 应用法律领域加权
        self._apply_legal_domain_weighting(all_keywords)
        
        # 6. 排序并返回结果
        sorted_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
        final_result = sorted_keywords[:top_k]
        
        # 更新缓存
        self._update_cache(cache_key, sorted_keywords)
        
        return final_result
    
    def _extract_tfidf_keywords(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """TF-IDF关键词提取"""
        if not self.jieba_available:
            return []
        
        try:
            keywords = jieba.analyse.extract_tags(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=['n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'ad']
            )
            return keywords
        except Exception as e:
            self.logger.error(f"TF-IDF提取失败: {e}")
            return []
    
    def _extract_textrank_keywords(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """TextRank关键词提取"""
        if not self.jieba_available:
            return []
        
        try:
            keywords = jieba.analyse.textrank(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=['n', 'nr', 'ns', 'nt', 'nz']
            )
            return keywords
        except Exception as e:
            self.logger.error(f"TextRank提取失败: {e}")
            return []
    
    def _extract_frequency_keywords(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """基于词频的关键词提取 (备用方案)"""
        try:
            # 使用jieba分词或简单的中文正则
            if self.jieba_available:
                words = [w for w in jieba.lcut(text) if len(w) >= 2]
            else:
                words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
            
            # 词频统计
            word_counter = Counter(words)
            total_words = sum(word_counter.values()) or 1
            
            # 转换为权重格式
            freq_keywords = [
                (word, count / total_words)
                for word, count in word_counter.most_common(top_k)
            ]
            
            return freq_keywords
            
        except Exception as e:
            self.logger.error(f"词频统计失败: {e}")
            return []
    
    def _extract_semantic_keywords(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """基于语义的关键词提取 (简化版KeyBERT)"""
        try:
            # 这里实现简化的语义关键词提取
            # 可以使用现有的语义模型来计算词汇与文档的相似度
            
            # 先用传统方法获取候选词汇
            if self.jieba_available:
                candidate_words = [w for w in jieba.lcut(text) if len(w) >= 2]
            else:
                candidate_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
            
            # 去重并限制数量
            unique_candidates = list(set(candidate_words))[:50]
            
            # 简单的启发式评分 (真正的KeyBERT需要更复杂的实现)
            semantic_scores = []
            for word in unique_candidates:
                # 基于词汇在法律词典中的权重
                base_score = self.dynamic_legal_dict['all_keywords'].get(word, 0.01)
                
                # 基于词汇长度的调整
                length_bonus = min(len(word) / 6, 0.2)
                
                # 基于词汇在文本中的位置 (前面的词汇更重要)
                position_bonus = 0.1 if text.find(word) < len(text) / 3 else 0
                
                final_score = base_score + length_bonus + position_bonus
                semantic_scores.append((word, final_score))
            
            # 排序并返回
            semantic_scores.sort(key=lambda x: x[1], reverse=True)
            return semantic_scores[:top_k]
            
        except Exception as e:
            self.logger.error(f"语义提取失败: {e}")
            return []
    
    def _apply_legal_domain_weighting(self, keywords_dict: Dict[str, float]):
        """应用法律领域权重加成"""
        
        # 获取动态词典
        all_legal_words = self.dynamic_legal_dict.get('all_keywords', {})
        high_weight_words = self.dynamic_legal_dict.get('high_weight', {})
        
        for word in keywords_dict:
            # 法律专业词汇加权
            if word in all_legal_words:
                legal_weight = all_legal_words[word]
                keywords_dict[word] *= (1 + legal_weight * 2)  # 根据法律权重加成
                
                # 高权重法律词汇额外加成
                if word in high_weight_words:
                    keywords_dict[word] *= 1.2
            
            # 基于规则的模式匹配加权
            legal_patterns = [
                (r'.*法$', 1.3),      # 以"法"结尾
                (r'.*罪$', 1.3),      # 以"罪"结尾  
                (r'.*权$', 1.2),      # 以"权"结尾
                (r'.*责任$', 1.3),    # 以"责任"结尾
                (r'^合同.*', 1.2),    # 以"合同"开头
                (r'^诉讼.*', 1.2),    # 以"诉讼"开头
            ]
            
            for pattern, multiplier in legal_patterns:
                if re.match(pattern, word):
                    keywords_dict[word] *= multiplier
                    break
    
    def _update_cache(self, cache_key: int, keywords: List[Tuple[str, float]]):
        """更新关键词缓存"""
        if len(self.keyword_cache) >= self.max_cache_size:
            # 删除最旧的缓存项
            oldest_key = next(iter(self.keyword_cache))
            del self.keyword_cache[oldest_key]
        
        self.keyword_cache[cache_key] = keywords
    
    def compute_keyword_similarity(self, query_text: str, document_text: str, 
                                 query_top_k: int = 8, doc_top_k: int = 15) -> float:
        """
        计算基于智能关键词提取的相似度
        
        Args:
            query_text: 查询文本
            document_text: 文档文本  
            query_top_k: 查询关键词数量
            doc_top_k: 文档关键词数量
            
        Returns:
            float: 相似度分数 [0, 1]
        """
        
        # 提取查询和文档的关键词
        query_keywords = dict(self.extract_keywords_multi_algorithm(query_text, query_top_k))
        doc_keywords = dict(self.extract_keywords_multi_algorithm(document_text, doc_top_k))
        
        if not query_keywords or not doc_keywords:
            return 0.0
        
        # 计算加权匹配分数
        total_query_weight = sum(query_keywords.values())
        matched_weight = 0.0
        
        for query_word, query_weight in query_keywords.items():
            if query_word in doc_keywords:
                # 直接匹配：取较小权重并给予高加成
                doc_weight = doc_keywords[query_word]
                match_score = min(query_weight, doc_weight) * 2.0
                matched_weight += match_score
                
            else:
                # 模糊匹配：检查包含关系
                fuzzy_score = 0.0
                for doc_word, doc_weight in doc_keywords.items():
                    if query_word in doc_word or doc_word in query_word:
                        fuzzy_score = max(fuzzy_score, doc_weight * 0.6)
                
                matched_weight += min(query_weight, fuzzy_score)
        
        # 计算相似度
        if total_query_weight > 0:
            similarity = matched_weight / total_query_weight
            
            # 法律领域匹配加成
            legal_bonus = self._compute_legal_match_bonus(query_keywords, doc_keywords)
            
            final_similarity = min(similarity + legal_bonus, 1.0)
            return final_similarity
        
        return 0.0
    
    def _compute_legal_match_bonus(self, query_keywords: Dict[str, float], 
                                 doc_keywords: Dict[str, float]) -> float:
        """计算法律领域匹配加成"""
        legal_matches = 0
        high_weight_words = self.dynamic_legal_dict.get('high_weight', {})
        
        for word in query_keywords:
            if word in doc_keywords and word in high_weight_words:
                legal_matches += 1
        
        # 每个高权重法律词匹配给予0.03加成，最多0.15
        return min(legal_matches * 0.03, 0.15)
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """获取关键词提取统计信息"""
        return {
            'jieba_available': self.jieba_available,
            'keybert_available': self.keybert_model is not None and self.keybert_model is not False,
            'dynamic_dict_size': len(self.dynamic_legal_dict.get('all_keywords', {})),
            'cache_size': len(self.keyword_cache),
            'algorithm_weights': self.algorithm_weights
        }

# 全局实例
_smart_keyword_extractor = None

def get_smart_keyword_extractor() -> SmartKeywordExtractor:
    """获取全局智能关键词提取器实例"""
    global _smart_keyword_extractor
    if _smart_keyword_extractor is None:
        _smart_keyword_extractor = SmartKeywordExtractor()
    return _smart_keyword_extractor