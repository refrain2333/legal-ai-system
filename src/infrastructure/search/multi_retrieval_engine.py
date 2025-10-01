#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多路召回融合引擎
整合混合搜索、Query2doc和HyDE三种搜索策略，实现智能的结果融合
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class MultiRetrievalEngine:
    """三路召回融合引擎

    整合以下三种搜索策略：
    1. 混合搜索 (Hybrid Search): BM25 + 向量搜索融合
    2. Query2doc搜索: LLM生成假设文档片段进行搜索
    3. HyDE搜索: LLM生成假设答案进行搜索

    通过加权融合和RRF(Reciprocal Rank Fusion)获得最终结果
    """

    def __init__(self, vector_engine, query2doc_enhancer, hyde_enhancer, config):
        """
        初始化多路召回引擎

        Args:
            vector_engine: 向量搜索引擎
            query2doc_enhancer: Query2doc增强器
            hyde_enhancer: HyDE增强器
            config: 配置对象
        """
        self.vector_engine = vector_engine
        self.query2doc_enhancer = query2doc_enhancer
        self.hyde_enhancer = hyde_enhancer
        self.config = config

        # 从配置获取权重
        self.hybrid_weight = config.HYBRID_WEIGHT
        self.query2doc_weight = config.QUERY2DOC_WEIGHT
        self.hyde_weight = config.HYDE_WEIGHT

        # 归一化权重
        total_weight = self.hybrid_weight + self.query2doc_weight + self.hyde_weight
        self.hybrid_weight /= total_weight
        self.query2doc_weight /= total_weight
        self.hyde_weight /= total_weight

        logger.info(f"多路召回引擎初始化完成")
        logger.info(f"  - 混合搜索权重: {self.hybrid_weight:.3f}")
        logger.info(f"  - Query2doc权重: {self.query2doc_weight:.3f}")
        logger.info(f"  - HyDE权重: {self.hyde_weight:.3f}")

    async def three_way_retrieval(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        执行三路召回融合搜索

        Args:
            query: 用户查询
            top_k: 返回结果数量

        Returns:
            融合后的搜索结果列表
        """
        start_time = time.time()

        try:
            logger.info(f"开始三路召回搜索: '{query}'")

            # 检查各组件状态
            self._check_components_status()

            # 并行执行三路搜索
            search_tasks = [
                self._hybrid_search_task(query, top_k * 2),
                self._query2doc_search_task(query, top_k * 2),
                self._hyde_search_task(query, top_k * 2)
            ]

            # 等待所有搜索完成
            results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # 处理搜索结果
            hybrid_results, query2doc_results, hyde_results = self._process_search_results(results)

            # 融合结果
            fused_results = self._fuse_results(
                hybrid_results=hybrid_results,
                query2doc_results=query2doc_results,
                hyde_results=hyde_results,
                top_k=top_k
            )

            end_time = time.time()
            duration = (end_time - start_time) * 1000

            logger.info(f"三路召回完成: {len(fused_results)}个结果，耗时{duration:.2f}ms")

            # 添加搜索元信息
            for result in fused_results:
                result['search_meta'] = {
                    'retrieval_method': 'three_way_fusion',
                    'duration_ms': duration,
                    'hybrid_weight': self.hybrid_weight,
                    'query2doc_weight': self.query2doc_weight,
                    'hyde_weight': self.hyde_weight
                }

            return fused_results

        except Exception as e:
            logger.error(f"三路召回失败: {e}")
            # 降级到混合搜索
            return await self._fallback_search(query, top_k)

    async def _hybrid_search_task(self, query: str, top_k: int) -> List[Dict]:
        """混合搜索任务"""
        try:
            logger.debug("执行混合搜索")
            results = await self.vector_engine.hybrid_search(query, top_k)

            # 标记来源
            for result in results:
                result['source'] = 'hybrid'
                result['original_query'] = query

            logger.debug(f"混合搜索完成: {len(results)}个结果")
            return results

        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []

    async def _query2doc_search_task(self, query: str, top_k: int) -> List[Dict]:
        """Query2doc搜索任务"""
        try:
            if not self.config.ENABLE_QUERY2DOC:
                logger.debug("Query2doc已禁用")
                return []

            logger.debug("执行Query2doc搜索")

            # 生成增强查询
            enhanced_query = await self.query2doc_enhancer.enhance_query(query)

            # 执行向量搜索
            results = await self.vector_engine.search(enhanced_query, top_k, include_content=True)

            # 标记来源和增强信息
            for result in results:
                result['source'] = 'query2doc'
                result['original_query'] = query
                result['enhanced_query'] = enhanced_query

            logger.debug(f"Query2doc搜索完成: {len(results)}个结果")
            return results

        except Exception as e:
            logger.error(f"Query2doc搜索失败: {e}")
            return []

    async def _hyde_search_task(self, query: str, top_k: int) -> List[Dict]:
        """HyDE搜索任务"""
        try:
            if not self.config.ENABLE_HYDE:
                logger.debug("HyDE已禁用")
                return []

            logger.debug("执行HyDE搜索")

            # 生成假设性答案
            hypothetical_answer = await self.hyde_enhancer.generate_hypothetical_answer(query)

            # 用假设答案进行向量搜索
            results = await self.vector_engine.search(hypothetical_answer, top_k, include_content=True)

            # 标记来源和假设答案
            for result in results:
                result['source'] = 'hyde'
                result['original_query'] = query
                result['hypothetical_answer'] = hypothetical_answer

            logger.debug(f"HyDE搜索完成: {len(results)}个结果")
            return results

        except Exception as e:
            logger.error(f"HyDE搜索失败: {e}")
            return []

    def _process_search_results(self, results: List) -> Tuple[List, List, List]:
        """
        处理搜索结果，分离成功和失败的结果

        Args:
            results: 三路搜索的原始结果

        Returns:
            (hybrid_results, query2doc_results, hyde_results)
        """
        hybrid_results = []
        query2doc_results = []
        hyde_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"搜索路径{i}失败: {result}")
                # 对应的结果设为空列表
                if i == 0:
                    hybrid_results = []
                elif i == 1:
                    query2doc_results = []
                elif i == 2:
                    hyde_results = []
            else:
                # 成功的结果
                if i == 0:
                    hybrid_results = result
                elif i == 1:
                    query2doc_results = result
                elif i == 2:
                    hyde_results = result

        return hybrid_results, query2doc_results, hyde_results

    def _fuse_results(self, hybrid_results: List, query2doc_results: List,
                     hyde_results: List, top_k: int) -> List[Dict]:
        """
        融合三路搜索结果

        Args:
            hybrid_results: 混合搜索结果
            query2doc_results: Query2doc搜索结果
            hyde_results: HyDE搜索结果
            top_k: 最终返回结果数量

        Returns:
            融合后的结果列表
        """
        logger.debug(f"开始融合结果: hybrid={len(hybrid_results)}, q2d={len(query2doc_results)}, hyde={len(hyde_results)}")

        # 结果字典，用于收集和融合
        results_dict = defaultdict(lambda: {
            'score': 0.0,
            'sources': [],
            'rank_positions': {},
            'original_result': None
        })

        # 融合混合搜索结果
        self._merge_results_with_rrf(
            results_dict, hybrid_results,
            weight=self.hybrid_weight,
            source='hybrid'
        )

        # 融合Query2doc搜索结果
        self._merge_results_with_rrf(
            results_dict, query2doc_results,
            weight=self.query2doc_weight,
            source='query2doc'
        )

        # 融合HyDE搜索结果
        self._merge_results_with_rrf(
            results_dict, hyde_results,
            weight=self.hyde_weight,
            source='hyde'
        )

        # 最终排序和选择
        final_results = self._final_rank_and_select(results_dict, top_k)

        logger.debug(f"融合完成: {len(final_results)}个最终结果")
        return final_results

    def _merge_results_with_rrf(self, results_dict: Dict, search_results: List,
                               weight: float, source: str):
        """
        使用RRF (Reciprocal Rank Fusion) 方法融合搜索结果

        Args:
            results_dict: 结果收集字典
            search_results: 单路搜索结果
            weight: 权重
            source: 来源标识
        """
        k = 60  # RRF参数

        for rank, result in enumerate(search_results):
            doc_id = result.get('id')
            if not doc_id:
                continue

            # RRF分数计算
            rrf_score = 1 / (k + rank + 1)
            weighted_score = rrf_score * weight

            # 原始相似度分数加权
            similarity_score = result.get('similarity', 0) * weight * 0.3

            # 总分数
            total_score = weighted_score + similarity_score

            # 更新结果字典
            if doc_id in results_dict:
                results_dict[doc_id]['score'] += total_score
                results_dict[doc_id]['sources'].append(source)
                results_dict[doc_id]['rank_positions'][source] = rank + 1
            else:
                results_dict[doc_id] = {
                    'score': total_score,
                    'sources': [source],
                    'rank_positions': {source: rank + 1},
                    'original_result': result.copy()
                }

    def _final_rank_and_select(self, results_dict: Dict, top_k: int) -> List[Dict]:
        """
        最终排序和选择结果

        Args:
            results_dict: 融合后的结果字典
            top_k: 返回结果数量

        Returns:
            最终排序后的结果列表
        """
        # 计算增强分数
        enhanced_results = []
        for doc_id, meta in results_dict.items():
            result = meta['original_result'].copy()

            # 基础融合分数
            result['fusion_score'] = meta['score']

            # 多路验证置信度 (出现在多少路搜索中)
            result['confidence'] = len(meta['sources']) / 3.0

            # 一致性分数 (在不同搜索中的排名一致性)
            consistency_score = self._calculate_consistency_score(meta['rank_positions'])
            result['consistency_score'] = consistency_score

            # 来源信息
            result['sources'] = meta['sources']
            result['rank_positions'] = meta['rank_positions']

            # 计算最终分数 (融合分数 + 置信度奖励 + 一致性奖励)
            confidence_bonus = result['confidence'] * 0.1
            consistency_bonus = consistency_score * 0.05
            result['final_score'] = result['fusion_score'] + confidence_bonus + consistency_bonus

            enhanced_results.append(result)

        # 按最终分数排序
        enhanced_results.sort(key=lambda x: x['final_score'], reverse=True)

        # 返回前top_k个结果
        return enhanced_results[:top_k]

    def _calculate_consistency_score(self, rank_positions: Dict) -> float:
        """
        计算排名一致性分数

        Args:
            rank_positions: 各搜索路径中的排名位置

        Returns:
            一致性分数 (0-1)
        """
        if len(rank_positions) <= 1:
            return 1.0

        positions = list(rank_positions.values())

        # 计算排名差异的标准差
        mean_pos = sum(positions) / len(positions)
        variance = sum((pos - mean_pos) ** 2 for pos in positions) / len(positions)
        std_dev = variance ** 0.5

        # 转换为0-1分数，差异越小分数越高
        consistency_score = max(0, 1 - (std_dev / 20))  # 20是经验值
        return consistency_score

    async def _fallback_search(self, query: str, top_k: int) -> List[Dict]:
        """
        降级搜索策略

        Args:
            query: 用户查询
            top_k: 返回结果数量

        Returns:
            降级搜索结果
        """
        logger.warning("执行降级搜索策略")

        try:
            # 尝试混合搜索
            results = await self.vector_engine.hybrid_search(query, top_k)
            for result in results:
                result['source'] = 'fallback_hybrid'
                result['search_meta'] = {'retrieval_method': 'fallback_hybrid'}
            return results

        except Exception as e:
            logger.error(f"降级搜索也失败: {e}")

            try:
                # 最后尝试纯向量搜索
                results = await self.vector_engine.search(query, top_k, include_content=True)
                for result in results:
                    result['source'] = 'fallback_vector'
                    result['search_meta'] = {'retrieval_method': 'fallback_vector'}
                return results

            except Exception as e2:
                logger.error(f"所有搜索方法都失败: {e2}")
                return []

    def _check_components_status(self):
        """检查各组件状态"""
        if not self.vector_engine:
            raise RuntimeError("向量搜索引擎未初始化")

        if self.config.ENABLE_QUERY2DOC and not self.query2doc_enhancer:
            logger.warning("Query2doc已启用但增强器未初始化")

        if self.config.ENABLE_HYDE and not self.hyde_enhancer:
            logger.warning("HyDE已启用但增强器未初始化")

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        获取检索统计信息

        Returns:
            统计信息字典
        """
        return {
            "weights": {
                "hybrid": self.hybrid_weight,
                "query2doc": self.query2doc_weight,
                "hyde": self.hyde_weight
            },
            "enabled_features": {
                "query2doc": self.config.ENABLE_QUERY2DOC,
                "hyde": self.config.ENABLE_HYDE
            },
            "components_status": {
                "vector_engine": self.vector_engine is not None,
                "query2doc_enhancer": self.query2doc_enhancer is not None,
                "hyde_enhancer": self.hyde_enhancer is not None
            }
        }

    def update_weights(self, hybrid_weight: float = None,
                      query2doc_weight: float = None,
                      hyde_weight: float = None):
        """
        动态更新权重配置

        Args:
            hybrid_weight: 混合搜索权重
            query2doc_weight: Query2doc权重
            hyde_weight: HyDE权重
        """
        if hybrid_weight is not None:
            self.hybrid_weight = hybrid_weight
        if query2doc_weight is not None:
            self.query2doc_weight = query2doc_weight
        if hyde_weight is not None:
            self.hyde_weight = hyde_weight

        # 重新归一化权重
        total_weight = self.hybrid_weight + self.query2doc_weight + self.hyde_weight
        if total_weight > 0:
            self.hybrid_weight /= total_weight
            self.query2doc_weight /= total_weight
            self.hyde_weight /= total_weight

        logger.info(f"权重已更新: hybrid={self.hybrid_weight:.3f}, q2d={self.query2doc_weight:.3f}, hyde={self.hyde_weight:.3f}")