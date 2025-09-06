#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能混合排序引擎 v2.0
结合OPTIMIZATION_GUIDE和SMART_OPTIMIZATION_PLAN的核心思路
实现：智能查询扩展 + 多信号融合排序
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pickle
import asyncio
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

class IntelligentHybridRankingService:
    """智能混合排序引擎 - 完整版"""
    
    def __init__(self):
        print("Initializing Intelligent Hybrid Ranking Service v2.0...")
        
        # 1. 基础组件初始化
        self.embedding_model = None  # 延迟初始化
        
        # 2. 加载映射数据
        self.mapping_data = self._load_mapping_data()
        self.precise_mappings = self._build_precise_mapping_index()
        self.fuzzy_mappings = self._build_fuzzy_mapping_index()
        
        # 3. 构建智能查询扩展索引
        self.query_expansion_index = self._build_query_expansion_index()
        
        # 4. 初始化多信号权重
        self.signal_weights = {
            'semantic': 0.5,        # 原始语义相似度 50%
            'expansion': 0.25,      # 查询扩展匹配 25%
            'mapping': 0.15,        # 映射关系加权 15%
            'keyword': 0.10         # 关键词匹配 10%
        }
        
        print("Smart Hybrid Ranking Service initialized successfully!")
    
    def _load_mapping_data(self) -> Dict:
        """加载映射表数据"""
        try:
            precise_df = pd.read_csv('data/raw/精确映射表.csv')
            fuzzy_df = pd.read_csv('data/raw/精确+模糊匹配映射表.csv')
            
            print(f"Loaded mapping data: {len(precise_df)} precise, {len(fuzzy_df)} total mappings")
            
            return {
                'precise': precise_df,
                'fuzzy': fuzzy_df,
                'precise_count': len(precise_df),
                'fuzzy_count': len(fuzzy_df)
            }
        except Exception as e:
            print(f"Warning: 映射表加载失败 - {e}")
            return {'precise': pd.DataFrame(), 'fuzzy': pd.DataFrame()}
    
    def _build_precise_mapping_index(self) -> Dict:
        """构建精确映射索引 - 使用ID映射修复"""
        print("Building precise mapping index with ID mapping...")
        
        try:
            # 加载ID映射关系
            import pickle
            with open('data/processed/id_mapping.pkl', 'rb') as f:
                id_mapping = pickle.load(f)
            
            print(f"Loaded ID mapping: {len(id_mapping)} entries")
            
            index = {}
            mapped_count = 0
            
            if not self.mapping_data['precise'].empty:
                for _, row in self.mapping_data['precise'].iterrows():
                    case_id_original = row['案例ID']
                    law_id_original = row['律法ID']
                    
                    # 使用ID映射转换为实际文档ID
                    case_id = id_mapping.get(case_id_original)
                    law_id = id_mapping.get(law_id_original)
                    
                    if case_id and law_id:  # 只有当两个ID都能找到映射时才建立关系
                        description = row.get('适用说明', '')
                        main_usage = row.get('主要适用', '否') == '是'
                        weight = 0.9 if main_usage else 0.7
                        
                        # 建立双向映射关系
                        if case_id not in index:
                            index[case_id] = []
                        if law_id not in index:
                            index[law_id] = []
                        
                        index[case_id].append({
                            'related_id': law_id,
                            'type': 'law',
                            'relation': 'precise',
                            'description': description,
                            'weight': weight
                        })
                        
                        index[law_id].append({
                            'related_id': case_id,
                            'type': 'case', 
                            'relation': 'precise',
                            'description': description,
                            'weight': weight
                        })
                        
                        mapped_count += 1
            
            print(f"Built precise mapping index: {len(index)} documents with mappings ({mapped_count} relationships)")
            return index
            
        except Exception as e:
            print(f"Error building precise mapping index: {e}")
            return {}
    
    def _build_fuzzy_mapping_index(self) -> Dict:
        """构建模糊映射索引 - 使用ID映射修复"""
        print("Building fuzzy mapping index with ID mapping...")
        
        try:
            # 加载ID映射关系
            import pickle
            with open('data/processed/id_mapping.pkl', 'rb') as f:
                id_mapping = pickle.load(f)
            
            index = {}
            mapped_count = 0
            
            if not self.mapping_data['fuzzy'].empty:
                for _, row in self.mapping_data['fuzzy'].iterrows():
                    case_id_original = row['案例ID']
                    law_id_original = row['律法ID']
                    is_precise = row.get('主要适用', '否') == '是'
                    
                    # 跳过已在精确映射中的关系
                    if not is_precise:
                        # 使用ID映射转换为实际文档ID
                        case_id = id_mapping.get(case_id_original)
                        law_id = id_mapping.get(law_id_original)
                        
                        if case_id and law_id:
                            if law_id not in index:
                                index[law_id] = []
                            if case_id not in index:
                                index[case_id] = []
                                
                            weight = 0.6  # 模糊映射权重较低
                            description = row.get('适用说明', '')
                            
                            index[law_id].append({
                                'related_id': case_id,
                                'type': 'case',
                                'relation': 'fuzzy',
                                'description': description,
                                'weight': weight
                            })
                            
                            index[case_id].append({
                                'related_id': law_id,
                                'type': 'law',
                                'relation': 'fuzzy',
                                'description': description,
                                'weight': weight
                            })
                            
                            mapped_count += 1
        
            print(f"Built fuzzy mapping index: {len(index)} documents with mappings ({mapped_count} relationships)")
            return index
            
        except Exception as e:
            print(f"Error building fuzzy mapping index: {e}")
            return {}
    
    def _build_query_expansion_index(self) -> Dict:
        """构建智能查询扩展索引 - 基于现有文档而非映射表"""
        print("Building intelligent query expansion index...")
        
        try:
            # 加载完整数据集
            with open('data/processed/full_dataset.pkl', 'rb') as f:
                full_data = pickle.load(f)
            
            if 'documents' not in full_data:
                print("Warning: No 'documents' key found in dataset")
                return {'pairs': [], 'embeddings': None, 'professional_terms': []}
                
            documents = full_data['documents']
            
            # 策略改变：直接从文档中创建口语化-专业术语对应关系
            # 思路：案例标题通常更口语化，法条标题更专业化
            expansion_pairs = []
            
            # 获取案例和法条
            case_docs = [doc for doc in documents if doc['type'] == 'case']
            law_docs = [doc for doc in documents if doc['type'] == 'law']
            
            print(f"Found {len(case_docs)} cases and {len(law_docs)} laws")
            
            # 创建扩展对：基于关键词匹配
            # 这里用简化方法：提取案例中的关键概念，匹配对应法条
            keywords_mapping = {
                # 刑法相关
                '打': ['故意伤害', '暴力', '人身伤害'],
                '偷': ['盗窃', '侵占', '财产犯罪'],
                '抢': ['抢劫', '抢夺', '暴力犯罪'], 
                '杀': ['故意杀人', '故意伤害致死'],
                
                # 民法相关
                '离婚': ['婚姻', '家庭', '财产分割'],
                '财产': ['继承', '分割', '共同财产'],
                '合同': ['违约', '责任', '合同法'],
                '工资': ['劳动', '劳务', '薪酬'],
                
                # 行政法相关
                '交通': ['道路', '车辆', '交通法'],
                '税': ['税收', '税法', '征收'],
            }
            
            # 基于关键词创建映射
            for colloquial, professional_terms in keywords_mapping.items():
                for term in professional_terms:
                    expansion_pairs.append({
                        'colloquial': colloquial,
                        'professional': term,
                        'confidence': 0.8,
                        'source': 'keyword_mapping',
                        'description': f'{colloquial} -> {term}'
                    })
            
            # 额外：从实际文档标题中提取更多对应关系
            for case_doc in case_docs[:100]:  # 限制数量，避免过多
                case_title = case_doc.get('title', '')
                if case_title and len(case_title) > 10:  # 过滤太短的标题
                    # 从案例标题中提取关键词
                    for keyword, professional_terms in keywords_mapping.items():
                        if keyword in case_title:
                            for term in professional_terms[:2]:  # 每个关键词最多2个扩展
                                expansion_pairs.append({
                                    'colloquial': case_title[:50],  # 截取案例标题
                                    'professional': term,
                                    'confidence': 0.7,
                                    'source': 'case_title_mapping',
                                    'description': f'Case: {case_title[:30]}... -> {term}'
                                })
                            break  # 每个案例只匹配一次
            
            print(f"Generated {len(expansion_pairs)} query expansion pairs")
            
            # 构建语义索引（延迟初始化embedding模型）
            expansion_index = {
                'pairs': expansion_pairs,
                'embeddings': None,  # 延迟计算
                'professional_terms': [pair['professional'] for pair in expansion_pairs]
            }
            
            return expansion_index
            
        except Exception as e:
            print(f"Error building query expansion index: {e}")
            return {'pairs': [], 'embeddings': None, 'professional_terms': []}
    
    def _ensure_embedding_model(self):
        """确保embedding模型已初始化"""
        if self.embedding_model is None:
            print("Initializing embedding model for query expansion...")
            self.embedding_model = SentenceTransformer('shibing624/text2vec-base-chinese')
            
            # 计算扩展索引的embeddings
            if self.query_expansion_index['embeddings'] is None and self.query_expansion_index['pairs']:
                colloquial_texts = [pair['colloquial'] for pair in self.query_expansion_index['pairs']]
                if colloquial_texts:
                    self.query_expansion_index['embeddings'] = self.embedding_model.encode(colloquial_texts)
                    print(f"Computed embeddings for {len(colloquial_texts)} expansion pairs")
    
    async def expand_user_query(self, user_query: str, max_expansions: int = 3) -> Dict:
        """智能查询扩展 - 核心功能"""
        self._ensure_embedding_model()
        
        if not self.query_expansion_index['pairs'] or self.query_expansion_index['embeddings'] is None:
            return {
                'original_query': user_query,
                'expanded_query': user_query,
                'expansions': [],
                'expansion_applied': False
            }
        
        try:
            # 1. 对用户查询进行语义编码
            query_embedding = self.embedding_model.encode([user_query])
            
            # 2. 计算与所有口语表达的相似度
            similarities = cosine_similarity(query_embedding, self.query_expansion_index['embeddings'])[0]
            
            # 3. 获取top-k最相似的专业术语
            top_indices = similarities.argsort()[-max_expansions:]
            expansions = []
            
            for idx in reversed(top_indices):  # 按相似度降序
                if similarities[idx] > 0.3:  # 相似度阈值
                    pair = self.query_expansion_index['pairs'][idx]
                    confidence = similarities[idx] * pair['confidence']  # 结合原始置信度
                    
                    expansions.append({
                        'term': pair['professional'],
                        'confidence': confidence,
                        'source_colloquial': pair['colloquial'],
                        'similarity': similarities[idx],
                        'description': pair.get('description', '')
                    })
            
            # 4. 构建扩展查询
            expansion_terms = [exp['term'] for exp in expansions]
            expanded_query = user_query
            if expansion_terms:
                expanded_query += " " + " ".join(expansion_terms)
            
            return {
                'original_query': user_query,
                'expanded_query': expanded_query,
                'expansions': expansions,
                'expansion_applied': len(expansions) > 0
            }
            
        except Exception as e:
            print(f"Error in query expansion: {e}")
            return {
                'original_query': user_query,
                'expanded_query': user_query,
                'expansions': [],
                'expansion_applied': False
            }
    
    def _extract_legal_keywords(self, text: str) -> List[str]:
        """智能提取法律关键词 - 混合方案 (TextRank + 专业术语)"""
        try:
            import jieba
            import jieba.analyse
            
            # 方案1: 使用TextRank算法提取语义关键词
            # allowPOS限制为名词和动词，更适合法律文本
            textrank_keywords = jieba.analyse.textrank(
                text, 
                topK=3,  # 只取前3个最重要的
                withWeight=False,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn')  # 名词、动词类
            )
            
            # 方案2: 法律专业术语匹配（更精准的术语）
            legal_terms = [
                '故意伤害', '故意杀人', '盗窃罪', '抢劫罪', '诈骗罪', '合同违约',
                '交通事故', '机动车', '人身损害', '财产损失', '劳动争议', '工资',
                '婚姻法', '离婚', '财产分割', '抚养费', '继承权', '房产纠纷',
                '行政处罚', '刑事责任', '民事责任', '赔偿责任'
            ]
            
            # 提取文本中出现的专业术语
            matched_terms = []
            text_lower = text.lower()
            for term in legal_terms:
                if term in text_lower:
                    matched_terms.append(term)
            
            # 方案3: 组合去重
            all_keywords = list(set(textrank_keywords + matched_terms))
            
            # 限制最多5个关键词，优先保留TextRank结果
            result = textrank_keywords[:3]  # TextRank前3个
            for term in matched_terms:
                if term not in result and len(result) < 5:
                    result.append(term)
            
            return result
            
        except ImportError:
            print("jieba未安装，使用备用关键词提取方案")
            # 备用方案：基础法律术语匹配
            basic_terms = [
                '合同', '违约', '责任', '赔偿', '伤害', '事故', '盗窃', 
                '诈骗', '交通', '劳动', '工资', '婚姻', '离婚', '财产'
            ]
            return [term for term in basic_terms if term in text.lower()][:3]
        except Exception as e:
            print(f"关键词提取出错，使用简化方案: {e}")
            return []
    
    def _calculate_keyword_boost(self, query: str, result: Dict) -> float:
        """计算关键词匹配加权分数 - 智能匹配版"""
        title = result.get('title', '')
        content_preview = result.get('content_preview', '')
        
        # 提取查询关键词
        query_keywords = self._extract_legal_keywords(query)
        
        if not query_keywords:
            return 0.0  # 🔧 修复：无关键词时返回0分，不是0.5分
        
        # 提取文档关键词
        doc_text = title + ' ' + content_preview
        doc_keywords = self._extract_legal_keywords(doc_text)
        
        if not doc_keywords:
            return 0.0
        
        # 智能匹配算法
        total_matches = 0
        max_possible_matches = len(query_keywords) * len(doc_keywords)
        
        for q_kw in query_keywords:
            for d_kw in doc_keywords:
                # 1. 完全匹配 (权重1.0)
                if q_kw == d_kw:
                    total_matches += 1.0
                # 2. 包含匹配 (权重0.8)
                elif q_kw in d_kw or d_kw in q_kw:
                    total_matches += 0.8
                # 3. 语义相关匹配 (权重0.6)
                elif self._are_keywords_related(q_kw, d_kw):
                    total_matches += 0.6
        
        if max_possible_matches == 0:
            return 0.0
            
        # 归一化匹配分数
        match_score = total_matches / max_possible_matches
        return min(match_score, 1.0)
    
    def _are_keywords_related(self, word1: str, word2: str) -> bool:
        """判断两个关键词是否语义相关"""
        # 定义语义相关词组
        semantic_groups = [
            # 刑法相关
            {'故意伤害', '伤害', '暴力', '殴打', '打击', '人身伤害'},
            {'盗窃', '偷', '偷窃', '盗窃罪', '财产犯罪'},
            {'诈骗', '欺诈', '诈骗罪', '虚假'},
            {'抢劫', '抢夺', '抢劫罪', '暴力犯罪'},
            
            # 民法相关
            {'合同', '违约', '合同违约', '责任', '赔偿'},
            {'交通', '事故', '车祸', '撞车', '交通事故', '机动车'},
            {'婚姻', '离婚', '财产分割', '抚养', '婚姻法'},
            {'劳动', '工资', '薪酬', '劳务', '劳动争议'},
            
            # 财产相关
            {'财产', '房产', '继承', '遗产', '房屋'},
            {'损失', '损害', '赔偿', '补偿'}
        ]
        
        # 检查是否在同一语义组
        for group in semantic_groups:
            if word1 in group and word2 in group:
                return True
        return False
    
    def _calculate_mapping_boost(self, doc_id: str) -> float:
        """计算映射关系加权分数"""
        boost_score = 0.0
        
        # 精确映射加权更高
        if doc_id in self.precise_mappings:
            boost_score += 0.8  # 精确映射基础分
            boost_score += min(len(self.precise_mappings[doc_id]) * 0.1, 0.2)  # 关联数量加权
        
        # 模糊映射加权较低
        elif doc_id in self.fuzzy_mappings:
            boost_score += 0.5  # 模糊映射基础分
            boost_score += min(len(self.fuzzy_mappings[doc_id]) * 0.05, 0.1)  # 关联数量加权
        
        return min(boost_score, 1.0)
    
    def _calculate_expansion_boost(self, expanded_query: str, result: Dict, expansion_info: Dict) -> float:
        """计算查询扩展匹配分数"""
        if not expansion_info['expansion_applied']:
            return 0.5  # 默认分数
        
        doc_text = result.get('title', '') + ' ' + result.get('content_preview', '')
        expansion_score = 0.0
        
        for expansion in expansion_info['expansions']:
            term = expansion['term']
            confidence = expansion['confidence']
            
            if term in doc_text:
                expansion_score += confidence
        
        # 归一化到0-1之间
        max_possible_score = sum(exp['confidence'] for exp in expansion_info['expansions'])
        if max_possible_score > 0:
            expansion_score = expansion_score / max_possible_score
        
        return min(expansion_score, 1.0)
    
    async def enhance_search_results(self, query: str, original_results: List[Dict], 
                                   expansion_info: Dict = None) -> List[Dict]:
        """增强检索结果 - 多信号融合"""
        if not original_results:
            return original_results
        
        # 如果没有提供扩展信息，先进行查询扩展
        if expansion_info is None:
            expansion_info = await self.expand_user_query(query)
        
        enhanced_results = []
        
        for result in original_results:
            enhanced_result = result.copy()
            doc_id = result.get('id', '')
            original_score = result.get('score', 0)
            
            # 1. 计算各个信号的分数
            mapping_score = self._calculate_mapping_boost(doc_id)
            keyword_score = self._calculate_keyword_boost(query, result)
            expansion_score = self._calculate_expansion_boost(
                expansion_info['expanded_query'], result, expansion_info
            )
            
            # 2. 真正动态权重分配算法 - 基于分数比例公平分配
            # 核心思路：每个信号的权重 = 该信号分数 / 所有信号总分数
            
            # 将所有信号分数归一化到相同量级 (0-1之间)
            normalized_scores = {
                'semantic': original_score,  # 语义分数已经是0-1之间
                'expansion': min(expansion_score, 1.0),  # 限制在0-1之间
                'mapping': min(mapping_score, 1.0),     # 限制在0-1之间
                'keyword': min(keyword_score, 1.0)      # 限制在0-1之间
            }
            
            # 计算总分数
            total_signal_score = sum(normalized_scores.values())
            
            # 动态计算权重：每个信号权重 = 该信号分数 / 总分数
            if total_signal_score > 0:
                semantic_weight = normalized_scores['semantic'] / total_signal_score
                expansion_weight = normalized_scores['expansion'] / total_signal_score
                mapping_weight = normalized_scores['mapping'] / total_signal_score
                keyword_weight = normalized_scores['keyword'] / total_signal_score
            else:
                # 兜底情况：如果所有分数都是0
                semantic_weight = 1.0
                expansion_weight = mapping_weight = keyword_weight = 0.0
            
            # 打印权重分配用于调试
            print(f"动态权重分配: 语义={semantic_weight:.3f}, 扩展={expansion_weight:.3f}, "
                  f"映射={mapping_weight:.3f}, 关键词={keyword_weight:.3f}")
            
            # 3. 计算最终分数
            final_score = (
                original_score * semantic_weight +
                expansion_score * expansion_weight +
                mapping_score * mapping_weight +
                keyword_score * keyword_weight
            )
            
            # 增强保障：如果其他信号太弱，确保不会拖累语义分数
            other_signals_contribution = expansion_score * expansion_weight + \
                                       mapping_score * mapping_weight + \
                                       keyword_score * keyword_weight
            
            # 如果其他信号的贡献很小（<0.05），直接使用语义分数
            if other_signals_contribution < 0.05:
                final_score = original_score
                semantic_weight = 1.0
                expansion_weight = mapping_weight = keyword_weight = 0.0
            
            # 3. 保存详细信息
            enhanced_result.update({
                'original_score': original_score,
                'final_score': final_score,
                'score': final_score,  # 更新主分数
                'score_breakdown': {
                    'semantic': original_score * semantic_weight,
                    'expansion': expansion_score * expansion_weight,
                    'mapping': mapping_score * mapping_weight,
                    'keyword': keyword_score * keyword_weight
                },
                'boost_details': {
                    'mapping_boost': mapping_score,
                    'keyword_boost': keyword_score,
                    'expansion_boost': expansion_score,
                    'has_precise_mapping': doc_id in self.precise_mappings,
                    'has_fuzzy_mapping': doc_id in self.fuzzy_mappings
                },
                'related_docs': self._get_related_documents(doc_id),
                'hybrid_enhanced': True
            })
            
            enhanced_results.append(enhanced_result)
        
        # 重新排序
        enhanced_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return enhanced_results
    
    def _get_related_documents(self, doc_id: str) -> List[Dict]:
        """获取相关文档信息"""
        related = []
        
        # 精确关联
        if doc_id in self.precise_mappings:
            for rel in self.precise_mappings[doc_id][:3]:  # 最多3个
                related.append({
                    'id': rel['related_id'],
                    'type': rel['type'],
                    'relation': 'precise',
                    'description': rel['description'],
                    'weight': rel['weight']
                })
        
        # 模糊关联 (如果精确关联不足)
        if len(related) < 3 and doc_id in self.fuzzy_mappings:
            remaining = 3 - len(related)
            for rel in self.fuzzy_mappings[doc_id][:remaining]:
                related.append({
                    'id': rel['related_id'],
                    'type': rel['type'],
                    'relation': 'fuzzy',
                    'description': rel['description'],
                    'weight': rel['weight']
                })
        
        return related
    
    def get_service_stats(self) -> Dict:
        """获取服务统计信息"""
        return {
            'version': '2.0',
            'precise_mappings_count': len(self.precise_mappings),
            'fuzzy_mappings_count': len(self.fuzzy_mappings),
            'expansion_pairs_count': len(self.query_expansion_index['pairs']),
            'signal_weights': self.signal_weights,
            'features': [
                'intelligent_query_expansion',
                'multi_signal_fusion',
                'mapping_based_ranking',
                'legal_keyword_matching'
            ]
        }
    
    def update_signal_weights(self, new_weights: Dict[str, float]):
        """更新信号权重（用于调优）"""
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"权重总和必须为1.0，当前为{total_weight}")
        
        self.signal_weights.update(new_weights)
        print(f"Updated signal weights: {self.signal_weights}")


# 全局服务实例
_intelligent_hybrid_service = None

async def get_intelligent_hybrid_service() -> IntelligentHybridRankingService:
    """获取智能混合排序服务实例"""
    global _intelligent_hybrid_service
    if _intelligent_hybrid_service is None:
        _intelligent_hybrid_service = IntelligentHybridRankingService()
    return _intelligent_hybrid_service