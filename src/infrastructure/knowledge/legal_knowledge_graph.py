#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级法律知识图谱
基于罪名-法条关系的智能查询扩展和关系推理
"""

import re
import logging
from typing import Dict, List, Any, Set, Optional, Tuple

logger = logging.getLogger(__name__)

class LegalKnowledgeGraph:
    """轻量级法律知识图谱"""

    def __init__(self, relation_data: Dict):
        """
        初始化知识图谱

        Args:
            relation_data: 关系抽取器生成的关系数据
        """
        self.crime_article_map = relation_data.get('crime_article_mapping', {})
        self.article_crime_map = relation_data.get('article_crime_mapping', {})

        # 配置参数
        self.confidence_threshold = 0.05  # 关系置信度阈值（5%）
        self.min_case_count = 2  # 最小案例数量

        # 统计信息
        self.total_crimes = len(self.crime_article_map)
        self.total_articles = len(self.article_crime_map)
        self.total_relations = sum(
            sum(articles.values()) for articles in self.crime_article_map.values()
        )

        # 构建反向查找索引
        self._build_search_indices()

        logger.info(f"知识图谱初始化完成: {self.total_crimes}种罪名, {self.total_articles}个法条, {self.total_relations}个关系")

    def _build_search_indices(self):
        """构建搜索索引，便于快速查找"""
        # 罪名关键词索引
        self.crime_keywords = {}
        for crime in self.crime_article_map.keys():
            # 添加完整罪名
            self.crime_keywords[crime] = crime
            self.crime_keywords[f"{crime}罪"] = crime

            # 添加罪名的部分匹配
            if len(crime) > 2:
                self.crime_keywords[crime[:2]] = crime

        # 法条编号索引
        self.article_keywords = {}
        for article in self.article_crime_map.keys():
            self.article_keywords[article] = article
            self.article_keywords[f"第{article}条"] = article
            self.article_keywords[f"{article}条"] = article

    def get_related_articles(self, crime: str, top_k: int = 5, include_confidence: bool = True) -> List[Dict]:
        """
        根据罪名获取相关法条 - 增强版支持稀少罪名

        Args:
            crime: 罪名
            top_k: 返回结果数量
            include_confidence: 是否包含置信度信息

        Returns:
            相关法条列表
        """
        crime_normalized = self._normalize_crime_name(crime)

        if crime_normalized not in self.crime_article_map:
            return []

        articles = self.crime_article_map[crime_normalized]
        total_cases = sum(articles.values())

        if total_cases == 0:
            return []

        # 按关联频次排序
        sorted_articles = sorted(articles.items(), key=lambda x: x[1], reverse=True)

        results = []
        for article_num, count in sorted_articles[:top_k]:
            confidence = count / total_cases

            # 应用稀少罪名友好的过滤策略
            if self._should_include_article(count, confidence, total_cases):
                result = {
                    'article_number': article_num,
                    'article_display': f"第{article_num}条",
                    'case_count': count,
                    'relation_type': 'crime_to_article'
                }

                if include_confidence:
                    # 应用稀少罪名置信度增强
                    enhanced_confidence = self._enhance_confidence_for_rare_crimes(confidence, total_cases)
                    result['confidence'] = round(enhanced_confidence, 3)
                    result['confidence_level'] = self._get_confidence_level(enhanced_confidence)
                    result['rare_crime'] = total_cases <= 5

                results.append(result)

        return results

    def _should_include_article(self, count: int, confidence: float, total_cases: int) -> bool:
        """
        判断是否应该包含该法条 - 对稀少罪名更宽松

        Args:
            count: 案例数量
            confidence: 置信度
            total_cases: 总案例数

        Returns:
            是否包含
        """
        if total_cases <= 5:
            # 稀少罪名：只要有1个案例就包含
            return count >= 1
        elif total_cases <= 20:
            # 中等频次罪名：放宽要求
            return confidence >= 0.02 and count >= 1
        else:
            # 高频罪名：保持原有标准
            return confidence >= self.confidence_threshold and count >= self.min_case_count

    def _enhance_confidence_for_rare_crimes(self, original_confidence: float, total_cases: int) -> float:
        """
        为稀少罪名增强置信度

        Args:
            original_confidence: 原始置信度
            total_cases: 总案例数

        Returns:
            增强后的置信度
        """
        if total_cases <= 3:
            # 极稀少罪名：大幅提升置信度
            return min(original_confidence * 3.0, 0.95)
        elif total_cases <= 10:
            # 稀少罪名：适度提升置信度
            return min(original_confidence * 2.0, 0.85)
        elif total_cases <= 20:
            # 较少罪名：轻微提升置信度
            return min(original_confidence * 1.5, 0.75)
        else:
            # 普通罪名：保持原置信度
            return original_confidence

    def get_related_crimes(self, article_num: str, top_k: int = 5, include_confidence: bool = True) -> List[Dict]:
        """
        根据法条获取相关罪名 - 增强版支持稀少罪名

        Args:
            article_num: 法条编号
            top_k: 返回结果数量
            include_confidence: 是否包含置信度信息

        Returns:
            相关罪名列表
        """
        article_normalized = self._normalize_article_number(article_num)

        if article_normalized not in self.article_crime_map:
            return []

        crimes = self.article_crime_map[article_normalized]
        total_cases = sum(crimes.values())

        if total_cases == 0:
            return []

        # 按关联频次排序
        sorted_crimes = sorted(crimes.items(), key=lambda x: x[1], reverse=True)

        results = []
        for crime, count in sorted_crimes[:top_k]:
            confidence = count / total_cases

            # 应用稀少罪名友好的过滤策略 - 对法条查罪名也宽松一些
            if self._should_include_crime(count, confidence, total_cases):
                result = {
                    'crime_name': crime,
                    'crime_display': f"{crime}罪",
                    'case_count': count,
                    'relation_type': 'article_to_crime'
                }

                if include_confidence:
                    # 对稀少罪名的置信度也进行适度增强
                    enhanced_confidence = self._enhance_confidence_for_rare_relations(confidence, count)
                    result['confidence'] = round(enhanced_confidence, 3)
                    result['confidence_level'] = self._get_confidence_level(enhanced_confidence)
                    result['rare_crime'] = count <= 5

                results.append(result)

        return results

    def _should_include_crime(self, count: int, confidence: float, total_cases: int) -> bool:
        """
        判断是否应该包含该罪名 - 对稀少罪名更宽松

        Args:
            count: 案例数量
            confidence: 置信度
            total_cases: 总案例数

        Returns:
            是否包含
        """
        if count <= 3:
            # 极稀少罪名：只要有1个案例就包含
            return count >= 1
        elif count <= 10:
            # 稀少罪名：放宽要求
            return confidence >= 0.01 and count >= 1
        else:
            # 普通罪名：适度放宽标准
            return confidence >= max(self.confidence_threshold * 0.5, 0.02) and count >= 1

    def _enhance_confidence_for_rare_relations(self, original_confidence: float, case_count: int) -> float:
        """
        为稀少关系增强置信度

        Args:
            original_confidence: 原始置信度
            case_count: 案例数量

        Returns:
            增强后的置信度
        """
        if case_count == 1:
            # 单一案例：给予基础置信度
            return min(original_confidence * 2.5, 0.75)
        elif case_count <= 3:
            # 极少案例：适度提升
            return min(original_confidence * 2.0, 0.70)
        elif case_count <= 10:
            # 较少案例：轻微提升
            return min(original_confidence * 1.5, 0.65)
        else:
            # 普通案例：保持原值
            return original_confidence

    def expand_query_with_relations(self, query: str) -> Dict[str, Any]:
        """
        基于知识图谱扩展查询

        Args:
            query: 用户查询

        Returns:
            查询扩展结果
        """
        expansion_results = {
            'original_query': query,
            'detected_entities': {
                'crimes': [],
                'articles': []
            },
            'related_articles': [],
            'related_crimes': [],
            'expansion_suggestions': [],
            'expanded_keywords': []
        }

        # 检测查询中的罪名
        detected_crimes = self._detect_crimes_in_query(query)
        expansion_results['detected_entities']['crimes'] = detected_crimes

        for crime in detected_crimes:
            related_articles = self.get_related_articles(crime, top_k=3)
            if related_articles:
                expansion_results['related_articles'].extend(related_articles)

                # 生成扩展建议
                for article in related_articles[:2]:  # 只取前2个最相关的
                    suggestion = f"建议同时查看{article['article_display']}"
                    expansion_results['expansion_suggestions'].append(suggestion)
                    expansion_results['expanded_keywords'].append(article['article_display'])

        # 检测查询中的法条
        detected_articles = self._detect_articles_in_query(query)
        expansion_results['detected_entities']['articles'] = detected_articles

        for article in detected_articles:
            related_crimes = self.get_related_crimes(article, top_k=3)
            if related_crimes:
                expansion_results['related_crimes'].extend(related_crimes)

                # 生成扩展建议
                for crime in related_crimes[:2]:  # 只取前2个最相关的
                    suggestion = f"建议同时查看{crime['crime_display']}"
                    expansion_results['expansion_suggestions'].append(suggestion)
                    expansion_results['expanded_keywords'].append(crime['crime_display'])

        # 去重
        expansion_results['expansion_suggestions'] = list(set(expansion_results['expansion_suggestions']))
        expansion_results['expanded_keywords'] = list(set(expansion_results['expanded_keywords']))

        return expansion_results

    def generate_expanded_query(self, original_query: str) -> str:
        """
        生成扩展后的查询字符串

        Args:
            original_query: 原始查询

        Returns:
            扩展后的查询字符串
        """
        expansion = self.expand_query_with_relations(original_query)

        expanded_terms = [original_query]
        expanded_terms.extend(expansion['expanded_keywords'])

        # 构建扩展查询（用空格分隔，便于搜索引擎处理）
        return " ".join(expanded_terms)

    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        # 计算连接度统计
        crime_connections = [len(articles) for articles in self.crime_article_map.values()]
        article_connections = [len(crimes) for crimes in self.article_crime_map.values()]

        return {
            'total_crimes': self.total_crimes,
            'total_articles': self.total_articles,
            'total_relations': self.total_relations,
            'avg_articles_per_crime': sum(crime_connections) / len(crime_connections) if crime_connections else 0,
            'avg_crimes_per_article': sum(article_connections) / len(article_connections) if article_connections else 0,
            'max_articles_per_crime': max(crime_connections) if crime_connections else 0,
            'max_crimes_per_article': max(article_connections) if article_connections else 0,
            'top_crimes': self._get_top_connected_crimes(5),
            'top_articles': self._get_top_connected_articles(5)
        }

    def _detect_crimes_in_query(self, query: str) -> List[str]:
        """检测查询中的罪名 - 优化版：精确匹配优先"""
        detected = []

        # 1. 精确匹配优先 - 检查是否是完整的罪名
        query_normalized = self._normalize_crime_name(query)
        if query_normalized in self.crime_article_map:
            detected.append(query_normalized)
            return detected  # 找到精确匹配，直接返回

        # 2. 检查是否是带"罪"后缀的查询
        if query.endswith('罪'):
            crime_without_suffix = query[:-1]
            if crime_without_suffix in self.crime_article_map:
                detected.append(crime_without_suffix)
                return detected

        # 3. 只有在没有精确匹配时，才进行模糊匹配
        # 但要过滤掉复合罪名（包含特殊字符的）
        for keyword, crime in self.crime_keywords.items():
            if keyword in query:
                # 过滤复合罪名：包含]、[、、等特殊字符的罪名
                if not any(char in crime for char in ['[', ']', '、', '，']):
                    detected.append(crime)

        # 4. 使用正则表达式匹配常见的罪名模式
        crime_patterns = [
            r'(\w+)罪',  # xxx罪
            r'(\w{2,4})犯罪',  # xxx犯罪
        ]

        for pattern in crime_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                normalized = self._normalize_crime_name(match)
                if normalized in self.crime_article_map:
                    # 同样过滤复合罪名
                    if not any(char in normalized for char in ['[', ']', '、', '，']):
                        detected.append(normalized)

        # 5. 如果仍然没有结果，进行宽松匹配但按相关度排序
        if not detected:
            potential_matches = []
            for crime in self.crime_article_map.keys():
                if query in crime:
                    # 计算匹配度：查询词在罪名中的比重
                    relevance = len(query) / len(crime)
                    potential_matches.append((crime, relevance))

            # 按相关度排序，只取最相关的
            if potential_matches:
                potential_matches.sort(key=lambda x: x[1], reverse=True)
                detected.append(potential_matches[0][0])

        return list(set(detected))  # 去重

    def _detect_articles_in_query(self, query: str) -> List[str]:
        """检测查询中的法条编号"""
        detected = []

        # 直接匹配
        for keyword, article in self.article_keywords.items():
            if keyword in query:
                detected.append(article)

        # 使用正则表达式匹配法条模式
        article_patterns = [
            r'第?\s*([0-9]+)\s*条',
            r'([0-9]+)\s*条',
            r'第([0-9]+)',
        ]

        for pattern in article_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                if match in self.article_crime_map:
                    detected.append(match)

        return list(set(detected))  # 去重

    def _normalize_crime_name(self, crime: str) -> str:
        """标准化罪名"""
        if not crime:
            return ""

        crime = crime.strip().replace('罪', '').replace('犯罪', '')
        return crime if len(crime) >= 2 else ""

    def _normalize_article_number(self, article: str) -> str:
        """标准化法条编号"""
        if not article:
            return ""

        # 提取数字
        match = re.search(r'([0-9]+)', str(article))
        return match.group(1) if match else ""

    def _get_confidence_level(self, confidence: float) -> str:
        """获取置信度等级"""
        if confidence >= 0.7:
            return "高"
        elif confidence >= 0.3:
            return "中"
        elif confidence >= 0.1:
            return "低"
        else:
            return "极低"

    def _get_top_connected_crimes(self, top_k: int) -> List[Dict]:
        """获取连接度最高的罪名"""
        crime_connections = {
            crime: len(articles) for crime, articles in self.crime_article_map.items()
        }

        sorted_crimes = sorted(crime_connections.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                'crime': crime,
                'display': f"{crime}罪",
                'connected_articles': count,
                'total_cases': sum(self.crime_article_map[crime].values())
            }
            for crime, count in sorted_crimes[:top_k]
        ]

    def _get_top_connected_articles(self, top_k: int) -> List[Dict]:
        """获取连接度最高的法条"""
        article_connections = {
            article: len(crimes) for article, crimes in self.article_crime_map.items()
        }

        sorted_articles = sorted(article_connections.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                'article': article,
                'display': f"第{article}条",
                'connected_crimes': count,
                'total_cases': sum(self.article_crime_map[article].values())
            }
            for article, count in sorted_articles[:top_k]
        ]

    def visualize_relations(self, entity: str, entity_type: str = 'auto') -> Dict[str, Any]:
        """
        生成实体关系的可视化数据

        Args:
            entity: 实体名称（罪名或法条）
            entity_type: 实体类型 ('crime', 'article', 'auto')

        Returns:
            可视化数据
        """
        if entity_type == 'auto':
            entity_type = self._detect_entity_type(entity)

        if entity_type == 'crime':
            related = self.get_related_articles(entity, top_k=10)
            center_node = {'id': entity, 'label': f"{entity}罪", 'type': 'crime'}
            relation_nodes = [
                {
                    'id': f"article_{item['article_number']}",
                    'label': item['article_display'],
                    'type': 'article',
                    'confidence': item.get('confidence', 0)
                }
                for item in related
            ]
            edges = [
                {
                    'source': entity,
                    'target': f"article_{item['article_number']}",
                    'weight': item.get('confidence', 0),
                    'label': f"{item['case_count']}案例"
                }
                for item in related
            ]

        elif entity_type == 'article':
            related = self.get_related_crimes(entity, top_k=10)
            center_node = {'id': entity, 'label': f"第{entity}条", 'type': 'article'}
            relation_nodes = [
                {
                    'id': f"crime_{item['crime_name']}",
                    'label': item['crime_display'],
                    'type': 'crime',
                    'confidence': item.get('confidence', 0)
                }
                for item in related
            ]
            edges = [
                {
                    'source': entity,
                    'target': f"crime_{item['crime_name']}",
                    'weight': item.get('confidence', 0),
                    'label': f"{item['case_count']}案例"
                }
                for item in related
            ]

        else:
            return {'error': f'Unknown entity type: {entity_type}'}

        return {
            'center_node': center_node,
            'nodes': [center_node] + relation_nodes,
            'edges': edges,
            'statistics': {
                'total_relations': len(relation_nodes),
                'entity_type': entity_type
            }
        }

    def _detect_entity_type(self, entity: str) -> str:
        """自动检测实体类型"""
        entity_normalized = self._normalize_crime_name(entity)
        if entity_normalized in self.crime_article_map:
            return 'crime'

        article_normalized = self._normalize_article_number(entity)
        if article_normalized in self.article_crime_map:
            return 'article'

        return 'unknown'

    def get_relation_case_count(self, crime: str, article: str) -> int:
        """
        获取特定罪名-法条关系的案例数量

        Args:
            crime: 罪名（如"诈骗"）
            article: 法条编号（如"266"）

        Returns:
            该关系的案例数量
        """
        crime_normalized = self._normalize_crime_name(crime)
        article_normalized = self._normalize_article_number(article)

        if (crime_normalized in self.crime_article_map and
            article_normalized in self.crime_article_map[crime_normalized]):
            return self.crime_article_map[crime_normalized][article_normalized]

        return 0

    def get_relation_details(self, crime: str, article: str) -> Dict[str, Any]:
        """
        获取特定罪名-法条关系的详细信息

        Args:
            crime: 罪名（如"诈骗"）
            article: 法条编号（如"266"）

        Returns:
            关系详细信息
        """
        crime_normalized = self._normalize_crime_name(crime)
        article_normalized = self._normalize_article_number(article)

        case_count = self.get_relation_case_count(crime, article)

        # 计算置信度
        confidence = 0.0
        if case_count > 0:
            # 基于案例数量计算置信度
            total_crime_cases = sum(self.crime_article_map.get(crime_normalized, {}).values())
            if total_crime_cases > 0:
                confidence = case_count / total_crime_cases

            # 应用稀有罪名增强
            confidence = self._enhance_confidence_for_rare_crimes(confidence, case_count)

        return {
            'crime': crime_normalized,
            'article': article_normalized,
            'case_count': case_count,
            'confidence': confidence,
            'exists': case_count > 0,
            'display_text': f"{crime}罪-第{article}条: {case_count}案例"
        }