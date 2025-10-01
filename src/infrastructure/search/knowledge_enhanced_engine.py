#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱增强搜索引擎
基于法律知识图谱的智能查询扩展和多路召回融合
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class KnowledgeEnhancedSearchEngine:
    """知识图谱增强的搜索引擎"""

    def __init__(self, multi_retrieval_engine, knowledge_graph, config):
        """
        初始化知识图谱增强搜索引擎

        Args:
            multi_retrieval_engine: 多路召回引擎
            knowledge_graph: 知识图谱实例
            config: 配置对象
        """
        self.multi_retrieval_engine = multi_retrieval_engine
        self.knowledge_graph = knowledge_graph
        self.config = config

        # 从配置获取权重参数
        self.original_weight = getattr(config, 'KG_ORIGINAL_WEIGHT', 0.5)
        self.related_article_weight = getattr(config, 'KG_RELATED_ARTICLE_WEIGHT', 0.3)
        self.related_crime_weight = getattr(config, 'KG_RELATED_CRIME_WEIGHT', 0.2)

        # 搜索统计
        self.search_stats = {
            'total_searches': 0,
            'kg_enhanced_searches': 0,
            'expansion_rate': 0.0,
            'avg_response_time': 0.0
        }

        logger.info(f"知识图谱增强搜索引擎初始化完成")
        logger.info(f"权重配置: 原始查询={self.original_weight}, 相关法条={self.related_article_weight}, 相关罪名={self.related_crime_weight}")

    async def knowledge_enhanced_search(self, query: str, top_k: int = 20,
                                      enable_expansion: bool = True) -> List[Dict]:
        """
        知识图谱增强搜索

        Args:
            query: 用户查询
            top_k: 返回结果数量
            enable_expansion: 是否启用知识图谱扩展

        Returns:
            增强搜索结果列表
        """
        start_time = time.time()
        self.search_stats['total_searches'] += 1

        try:
            # 检查知识图谱是否可用
            if not self.knowledge_graph or not enable_expansion:
                logger.debug("知识图谱不可用或未启用，降级到普通搜索")
                return await self.multi_retrieval_engine.three_way_retrieval(query, top_k)

            # 1. 基于知识图谱分析查询
            query_expansion = self.knowledge_graph.expand_query_with_relations(query)

            # 如果没有识别到任何实体，直接使用原始搜索
            if not query_expansion['detected_entities']['crimes'] and not query_expansion['detected_entities']['articles']:
                logger.debug(f"查询中未检测到法律实体，使用原始搜索: {query}")
                return await self.multi_retrieval_engine.three_way_retrieval(query, top_k)

            self.search_stats['kg_enhanced_searches'] += 1
            logger.info(f"检测到法律实体，启用知识图谱增强: {query_expansion['detected_entities']}")

            # 2. 执行多路搜索策略
            search_results = {}

            # 路径1: 原始查询搜索
            original_results = await self.multi_retrieval_engine.three_way_retrieval(query, top_k)
            self._merge_results_with_weight(search_results, original_results,
                                          self.original_weight, "original_query")

            # 路径2: 基于相关法条的搜索
            for article_info in query_expansion['related_articles']:
                article_query = article_info['article_display']
                confidence = article_info.get('confidence', 0.5)

                article_results = await self.multi_retrieval_engine.three_way_retrieval(
                    article_query, max(top_k // 3, 5)
                )

                # 根据置信度调整权重
                adjusted_weight = self.related_article_weight * confidence
                self._merge_results_with_weight(search_results, article_results,
                                              adjusted_weight, f"related_article_{article_info['article_number']}")

            # 路径3: 基于相关罪名的搜索
            for crime_info in query_expansion['related_crimes']:
                crime_query = crime_info['crime_display']
                confidence = crime_info.get('confidence', 0.5)

                crime_results = await self.multi_retrieval_engine.three_way_retrieval(
                    crime_query, max(top_k // 3, 5)
                )

                # 根据置信度调整权重
                adjusted_weight = self.related_crime_weight * confidence
                self._merge_results_with_weight(search_results, crime_results,
                                              adjusted_weight, f"related_crime_{crime_info['crime_name']}")

            # 3. 最终排序和多样性处理
            final_results = self._final_ranking_with_diversity(search_results, top_k)

            # 4. 添加知识图谱元信息
            for result in final_results:
                result['knowledge_expansion'] = query_expansion
                result['kg_enhanced'] = True
                result['expansion_paths'] = result.get('kg_sources', [])

            # 5. 更新统计信息
            duration = time.time() - start_time
            self._update_search_stats(duration, len(final_results), query_expansion)

            logger.info(f"知识图谱增强搜索完成: {len(final_results)}个结果，耗时{duration:.2f}s")
            return final_results

        except Exception as e:
            logger.error(f"知识图谱增强搜索失败: {e}")
            # 降级到原始三路召回
            return await self.multi_retrieval_engine.three_way_retrieval(query, top_k)

    async def get_entity_related_documents(self, entity: str, entity_type: str = 'auto',
                                         top_k: int = 10) -> List[Dict]:
        """
        获取与特定实体相关的文档

        Args:
            entity: 实体名称（罪名或法条）
            entity_type: 实体类型 ('crime', 'article', 'auto')
            top_k: 返回结果数量

        Returns:
            相关文档列表
        """
        try:
            if entity_type == 'auto':
                entity_type = self.knowledge_graph._detect_entity_type(entity)

            if entity_type == 'crime':
                # 获取相关法条
                related_articles = self.knowledge_graph.get_related_articles(entity, top_k=5)
                search_queries = [entity, f"{entity}罪"]
                search_queries.extend([art['article_display'] for art in related_articles])

            elif entity_type == 'article':
                # 获取相关罪名
                related_crimes = self.knowledge_graph.get_related_crimes(entity, top_k=5)
                search_queries = [f"第{entity}条"]
                search_queries.extend([crime['crime_display'] for crime in related_crimes])

            else:
                # 未识别实体类型，直接搜索
                search_queries = [entity]

            # 执行并行搜索
            all_results = {}
            for i, query in enumerate(search_queries):
                results = await self.multi_retrieval_engine.three_way_retrieval(query, top_k // 2)
                weight = 1.0 if i == 0 else 0.5  # 主查询权重更高
                self._merge_results_with_weight(all_results, results, weight, f"entity_search_{i}")

            # 排序并返回结果
            final_results = self._final_ranking_with_diversity(all_results, top_k)

            # 添加实体信息
            for result in final_results:
                result['entity_context'] = {
                    'entity': entity,
                    'entity_type': entity_type,
                    'search_strategy': 'entity_focused'
                }

            return final_results

        except Exception as e:
            logger.error(f"实体相关文档搜索失败: {e}")
            return []

    def _merge_results_with_weight(self, results_dict: Dict, new_results: List,
                                 weight: float, source: str):
        """
        按权重合并搜索结果

        Args:
            results_dict: 累积结果字典
            new_results: 新搜索结果
            weight: 权重
            source: 结果来源
        """
        for result in new_results:
            doc_id = result.get('id', result.get('document_id', ''))
            if not doc_id:
                continue

            similarity = result.get('similarity', result.get('score', 0))
            weighted_score = similarity * weight

            if doc_id in results_dict:
                # 累加分数
                results_dict[doc_id]['total_score'] += weighted_score
                results_dict[doc_id]['kg_sources'].append(source)
                results_dict[doc_id]['kg_boost'] = True

                # 保持最高的原始相似度
                if similarity > results_dict[doc_id]['max_similarity']:
                    results_dict[doc_id]['max_similarity'] = similarity
                    results_dict[doc_id]['best_result'] = result

            else:
                results_dict[doc_id] = {
                    'total_score': weighted_score,
                    'max_similarity': similarity,
                    'kg_sources': [source],
                    'kg_boost': source != 'original_query',
                    'best_result': result.copy(),
                    'appearance_count': 1
                }

            # 统计出现次数
            results_dict[doc_id]['appearance_count'] = len(results_dict[doc_id]['kg_sources'])

    def _final_ranking_with_diversity(self, results_dict: Dict, top_k: int) -> List[Dict]:
        """
        最终排序，考虑多样性和相关性 - 增强版支持稀少罪名显示

        Args:
            results_dict: 结果字典
            top_k: 返回数量

        Returns:
            最终排序结果
        """
        # 应用自适应权重加成
        results_dict = self._apply_adaptive_weighting(results_dict)

        # 按总分排序
        sorted_results = sorted(
            results_dict.items(),
            key=lambda x: (x[1]['total_score'], x[1]['appearance_count'], x[1]['max_similarity']),
            reverse=True
        )

        final_results = []
        article_count = 0
        case_count = 0
        max_articles = max(top_k // 2, 1)
        max_cases = max(top_k // 2, 1)

        for doc_id, meta in sorted_results:
            if len(final_results) >= top_k:
                break

            result = meta['best_result'].copy()

            # 添加知识图谱增强信息
            result['kg_total_score'] = round(meta['total_score'], 4)
            result['kg_sources'] = meta['kg_sources']
            result['kg_boost'] = meta['kg_boost']
            result['kg_appearance_count'] = meta['appearance_count']
            result['kg_confidence'] = min(meta['total_score'], 1.0)
            result['kg_rare_boost'] = meta.get('rare_boost', False)

            # 维持法条和案例的平衡
            is_article = 'article' in doc_id.lower()
            is_case = 'case' in doc_id.lower()

            if is_article and article_count < max_articles:
                final_results.append(result)
                article_count += 1
            elif is_case and case_count < max_cases:
                final_results.append(result)
                case_count += 1
            elif len(final_results) < top_k:
                # 填充剩余位置
                final_results.append(result)

        return final_results

    def _apply_adaptive_weighting(self, results_dict: Dict) -> Dict:
        """
        应用自适应权重策略 - 为稀少但相关的内容提升权重

        Args:
            results_dict: 原始结果字典

        Returns:
            权重调整后的结果字典
        """
        if not results_dict:
            return results_dict

        # 计算结果数量分布
        total_results = len(results_dict)
        scores = [meta['total_score'] for meta in results_dict.values()]

        if not scores:
            return results_dict

        avg_score = sum(scores) / len(scores)
        max_score = max(scores)

        # 自适应策略参数
        if total_results <= 3:
            # 极少结果：大幅提升权重，确保显示
            rare_boost_factor = 2.5
            min_boost_threshold = 0.01
        elif total_results <= 10:
            # 较少结果：适度提升权重
            rare_boost_factor = 1.8
            min_boost_threshold = 0.05
        elif total_results <= 50:
            # 中等结果：轻微提升权重
            rare_boost_factor = 1.3
            min_boost_threshold = 0.1
        else:
            # 大量结果：保持原有策略，只对非常匹配的提升
            rare_boost_factor = 1.1
            min_boost_threshold = 0.2

        # 应用权重调整
        for doc_id, meta in results_dict.items():
            original_score = meta['total_score']

            # 稀少内容检测条件
            is_rare_but_relevant = (
                total_results <= 10 or  # 总结果少
                (original_score >= min_boost_threshold and total_results <= 50) or  # 中等相关且结果不多
                any('original_query' in source for source in meta['kg_sources'])  # 原始查询匹配
            )

            if is_rare_but_relevant:
                # 计算动态提升倍数
                if original_score < 0.1:
                    # 低分但相关的内容，给予较大提升
                    boost_multiplier = rare_boost_factor * 1.5
                elif original_score < 0.3:
                    # 中等分数，给予标准提升
                    boost_multiplier = rare_boost_factor
                else:
                    # 高分内容，给予轻微提升
                    boost_multiplier = min(rare_boost_factor, 1.2)

                # 应用提升，但不超过最高分的1.5倍
                boosted_score = min(original_score * boost_multiplier, max_score * 1.5)
                meta['total_score'] = boosted_score
                meta['rare_boost'] = True

                logger.debug(f"稀少内容权重提升: {doc_id} {original_score:.4f} -> {boosted_score:.4f}")
            else:
                meta['rare_boost'] = False

        return results_dict

    def _update_search_stats(self, duration: float, result_count: int, query_expansion: Dict):
        """更新搜索统计信息"""
        try:
            # 更新平均响应时间
            total_searches = self.search_stats['total_searches']
            current_avg = self.search_stats['avg_response_time']
            self.search_stats['avg_response_time'] = (
                (current_avg * (total_searches - 1) + duration) / total_searches
            )

            # 更新扩展率
            if self.search_stats['total_searches'] > 0:
                self.search_stats['expansion_rate'] = (
                    self.search_stats['kg_enhanced_searches'] / self.search_stats['total_searches']
                )

        except Exception as e:
            logger.warning(f"更新搜索统计失败: {e}")

    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        graph_stats = self.knowledge_graph.get_graph_statistics() if self.knowledge_graph else {}

        return {
            'search_performance': {
                'total_searches': self.search_stats['total_searches'],
                'kg_enhanced_searches': self.search_stats['kg_enhanced_searches'],
                'expansion_rate': round(self.search_stats['expansion_rate'], 3),
                'avg_response_time_ms': round(self.search_stats['avg_response_time'] * 1000, 2)
            },
            'knowledge_graph': graph_stats,
            'weight_configuration': {
                'original_weight': self.original_weight,
                'related_article_weight': self.related_article_weight,
                'related_crime_weight': self.related_crime_weight
            }
        }

    async def explain_search_reasoning(self, query: str) -> Dict[str, Any]:
        """
        解释搜索推理过程

        Args:
            query: 查询文本

        Returns:
            搜索推理解释
        """
        try:
            # 分析查询
            query_expansion = self.knowledge_graph.expand_query_with_relations(query)

            explanation = {
                'original_query': query,
                'detected_entities': query_expansion['detected_entities'],
                'reasoning_steps': [],
                'search_strategies': [],
                'expected_enhancements': []
            }

            # 推理步骤
            if query_expansion['detected_entities']['crimes']:
                for crime in query_expansion['detected_entities']['crimes']:
                    related_articles = self.knowledge_graph.get_related_articles(crime, top_k=3)
                    if related_articles:
                        explanation['reasoning_steps'].append(
                            f"检测到罪名'{crime}'，将扩展搜索相关法条: {', '.join([art['article_display'] for art in related_articles])}"
                        )
                        explanation['search_strategies'].append('crime_to_article_expansion')

            if query_expansion['detected_entities']['articles']:
                for article in query_expansion['detected_entities']['articles']:
                    related_crimes = self.knowledge_graph.get_related_crimes(article, top_k=3)
                    if related_crimes:
                        explanation['reasoning_steps'].append(
                            f"检测到法条'{article}'，将扩展搜索相关罪名: {', '.join([crime['crime_display'] for crime in related_crimes])}"
                        )
                        explanation['search_strategies'].append('article_to_crime_expansion')

            # 预期增强效果
            if explanation['reasoning_steps']:
                explanation['expected_enhancements'] = [
                    "提高搜索结果的完整性",
                    "发现隐藏的相关内容",
                    "提供更全面的法律参考"
                ]
            else:
                explanation['reasoning_steps'].append("查询中未检测到明确的法律实体，将使用标准搜索")
                explanation['search_strategies'].append('standard_search')

            return explanation

        except Exception as e:
            logger.error(f"搜索推理解释失败: {e}")
            return {
                'original_query': query,
                'error': str(e),
                'fallback': '使用标准搜索'
            }