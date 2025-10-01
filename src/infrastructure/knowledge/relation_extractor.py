#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版：罪名-法条关系抽取器
从现有案例数据中抽取罪名与法条的关联关系，构建知识图谱基础数据
修复了原版本的数据质量问题和逻辑缺陷
"""

import re
import logging
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class RelationExtractor:
    """关系抽取器 - 修复版，解决数据质量问题"""

    def __init__(self, data_loader):
        """
        初始化关系抽取器

        Args:
            data_loader: 数据加载器实例
        """
        self.data_loader = data_loader
        self.crime_article_mapping = defaultdict(lambda: defaultdict(int))  # 罪名->法条->频次
        self.article_crime_mapping = defaultdict(lambda: defaultdict(int))  # 法条->罪名->频次

        # 罪名标准化映射（扩展版）
        self.crime_normalization = {
            '盗窃': '盗窃',
            '盗窃罪': '盗窃',
            '故意伤害': '故意伤害', 
            '故意伤害罪': '故意伤害',
            '交通肇事': '交通肇事',
            '交通肇事罪': '交通肇事',
            '诈骗': '诈骗',
            '诈骗罪': '诈骗',
            '抢劫': '抢劫',
            '抢劫罪': '抢劫',
            '强奸': '强奸',
            '强奸罪': '强奸',
            '故意杀人': '故意杀人',
            '故意杀人罪': '故意杀人',
            '危险驾驶': '危险驾驶',
            '危险驾驶罪': '危险驾驶',
            '寻衅滋事': '寻衅滋事',
            '寻衅滋事罪': '寻衅滋事',
            '聚众斗殴': '聚众斗殴',
            '聚众斗殴罪': '聚众斗殴',
            '受贿': '受贿',
            '受贿罪': '受贿',
            '贪污': '贪污', 
            '贪污罪': '贪污',
            '行贿': '行贿',
            '行贿罪': '行贿',
            '非法经营': '非法经营',
            '非法经营罪': '非法经营',
            '合同诈骗': '合同诈骗',
            '合同诈骗罪': '合同诈骗',
            '滥用职权': '滥用职权',
            '滥用职权罪': '滥用职权'
        }
        
        # 刑法条文类型分类（用于验证合理性）
        self.article_categories = {
            'general': list(range(1, 21)),        # 总则（1-20条）
            'property': list(range(264, 277)),    # 财产犯罪
            'person': list(range(232, 263)),      # 人身犯罪  
            'drug': list(range(347, 358)),        # 毒品犯罪
            'corruption': list(range(382, 397)),  # 贪污贿赂
            'economic': list(range(224, 232)),    # 经济犯罪
            'public_order': list(range(290, 307)) # 公共秩序
        }

    def extract_relations_from_cases(self) -> Dict[str, Any]:
        """
        从案例数据中抽取罪名-法条关系 - 修复版
        
        关键修复：
        1. 直接使用meta.relevant_articles而不是从text解析
        2. 添加法条-罪名关联的合理性验证
        3. 过滤明显错误的关联

        Returns:
            包含关系映射和统计信息的字典
        """
        logger.info("开始从案例数据中抽取罪名-法条关系（修复版）...")

        try:
            # 加载干净的JSON数据
            cases_file_path = Path("data/cases/legal_cases.json")
            logger.info(f"从 {cases_file_path} 加载案例数据...")

            if not cases_file_path.exists():
                logger.error(f"关键数据文件不存在: {cases_file_path}")
                return self._create_empty_result()

            with open(cases_file_path, 'r', encoding='utf-8') as f:
                # 每行一个JSON对象的格式
                cases_data = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            case = json.loads(line)
                            cases_data.append(case)
                        except json.JSONDecodeError as e:
                            logger.warning(f"第{line_num}行JSON解析失败: {e}")
                            continue

            if not cases_data:
                logger.error("无法获取案例数据")
                return self._create_empty_result()

            logger.info(f"成功加载 {len(cases_data)} 个案例，开始抽取关系...")

            processed_count = 0
            relation_count = 0
            filtered_count = 0  # 被过滤的不合理关联数

            for case in cases_data:
                try:
                    # 从meta字段直接提取标准化数据
                    meta = case.get('meta', {})
                    
                    # 提取罪名
                    accusations = meta.get('accusation', [])
                    if not accusations:
                        continue
                        
                    # 提取相关法条（直接使用meta中的数据）
                    relevant_articles = meta.get('relevant_articles', [])
                    if not relevant_articles:
                        continue

                    # 构建关系映射
                    for crime in accusations:
                        crime_normalized = self._normalize_crime_name(crime)
                        if not crime_normalized:
                            continue
                            
                        for article_num in relevant_articles:
                            article_str = str(article_num)
                            
                            # 关键修复：验证法条-罪名关联的合理性
                            if self._is_valid_crime_article_relation(crime_normalized, article_num):
                                # 建立双向映射
                                self.crime_article_mapping[crime_normalized][article_str] += 1
                                self.article_crime_mapping[article_str][crime_normalized] += 1
                                relation_count += 1
                            else:
                                filtered_count += 1
                                logger.debug(f"过滤不合理关联: {crime_normalized} <-> 第{article_num}条")

                    processed_count += 1

                    if processed_count % 1000 == 0:
                        logger.info(f"已处理 {processed_count} 个案例，抽取到 {relation_count} 个有效关系，过滤 {filtered_count} 个无效关系")

                except Exception as e:
                    logger.warning(f"处理案例时出错: {e}")
                    continue

            logger.info(f"关系抽取完成！")
            logger.info(f"- 处理案例: {processed_count}")
            logger.info(f"- 有效关系: {relation_count}")
            logger.info(f"- 过滤关系: {filtered_count}")
            logger.info(f"- 数据质量: {relation_count/(relation_count+filtered_count)*100:.1f}%")

            return self._generate_statistics()

        except Exception as e:
            logger.error(f"关系抽取失败: {e}", exc_info=True)
            return self._create_empty_result()

    def _is_valid_crime_article_relation(self, crime: str, article_num: int) -> bool:
        """
        验证罪名-法条关联的合理性
        
        Args:
            crime: 标准化罪名
            article_num: 法条编号
            
        Returns:
            是否为合理的关联
        """
        # 基础验证：法条编号范围
        if not (1 <= article_num <= 451):
            return False
            
        # 规则1：总则条款（1-20条）通常不直接对应具体罪名
        # 例外：某些总则条款可能在特殊情况下相关
        if 1 <= article_num <= 20:
            # 允许少数例外情况，但要求更高的频次阈值
            return False  # 暂时完全过滤，避免噪音
            
        # 规则2：根据罪名类型验证法条范围的合理性
        crime_article_rules = {
            '盗窃': [264, 269, 270, 271],  # 盗窃相关法条
            '抢劫': [263, 267, 269],       # 抢劫相关法条  
            '诈骗': [266],                  # 诈骗罪
            '故意伤害': [234, 235],        # 故意伤害罪
            '故意杀人': [232, 233],        # 故意杀人罪
            '交通肇事': [133],             # 交通肇事罪
            '危险驾驶': [133],             # 危险驾驶罪
            '受贿': [383, 385, 386, 388],  # 受贿相关
            '贪污': [382, 383, 384],       # 贪污相关
            '行贿': [389, 390, 391, 392], # 行贿相关
            '寻衅滋事': [293],             # 寻衅滋事罪
            '聚众斗殴': [292],             # 聚众斗殴罪
            '非法经营': [225],             # 非法经营罪
            '合同诈骗': [224],             # 合同诈骗罪
        }
        
        # 如果有明确的法条规则，检查是否在允许范围内
        if crime in crime_article_rules:
            allowed_articles = crime_article_rules[crime]
            # 允许核心法条的相邻条款（±5范围内）
            extended_range = set()
            for core_article in allowed_articles:
                extended_range.update(range(max(1, core_article-5), min(452, core_article+6)))
            
            if article_num not in extended_range:
                return False
        
        # 规则3：过滤明显错误的法条编号
        suspicious_patterns = [
            article_num > 451,  # 超出刑法范围
            article_num in [500, 485, 499, 425, 410],  # 明显不存在的法条
        ]
        
        if any(suspicious_patterns):
            return False
            
        return True

    def _normalize_crime_name(self, crime: str) -> str:
        """标准化罪名 - 增强版"""
        if not crime:
            return ""

        crime = crime.strip()
        
        # 处理特殊格式的罪名
        if crime.startswith('[') and crime.endswith(']'):
            # 例如: "[走私、贩卖、运输、制造]毒品" -> "走私、贩卖、运输、制造毒品"
            crime = crime[1:-1]  # 去掉方括号
            
        # 使用预定义映射
        if crime in self.crime_normalization:
            return self.crime_normalization[crime]

        # 移除"罪"后缀进行标准化
        normalized = crime.replace('罪', '').strip()

        # 过滤掉过短的罪名
        if len(normalized) < 2:
            return ""

        return normalized

    def _generate_statistics(self) -> Dict[str, Any]:
        """生成关系统计信息 - 增强版"""
        total_relations = sum(
            sum(articles.values()) for articles in self.crime_article_mapping.values()
        )

        # 转换为普通字典以便序列化
        crime_article_dict = {
            crime: dict(articles) for crime, articles in self.crime_article_mapping.items()
        }
        article_crime_dict = {
            article: dict(crimes) for article, crimes in self.article_crime_mapping.items()
        }

        # 数据质量分析
        quality_stats = self._analyze_data_quality()

        stats = {
            'success': True,
            'total_crimes': len(self.crime_article_mapping),
            'total_articles': len(self.article_crime_mapping),
            'total_relations': total_relations,
            'crime_article_mapping': crime_article_dict,
            'article_crime_mapping': article_crime_dict,
            'extraction_summary': {
                'most_frequent_crimes': self._get_top_crimes(10),
                'most_referenced_articles': self._get_top_articles(10),
                'avg_articles_per_crime': total_relations / len(self.crime_article_mapping) if self.crime_article_mapping else 0,
                'avg_crimes_per_article': total_relations / len(self.article_crime_mapping) if self.article_crime_mapping else 0
            },
            'data_quality': quality_stats
        }

        logger.info(f"修复版知识图谱统计: {stats['total_crimes']}种罪名, {stats['total_articles']}个法条, {stats['total_relations']}个关系")
        return stats

    def _analyze_data_quality(self) -> Dict[str, Any]:
        """分析数据质量"""
        quality_issues = []
        
        # 检查可能的总则条款关联
        general_articles = [str(i) for i in range(1, 21)]
        general_relations = sum(
            sum(crimes.values()) for article, crimes in self.article_crime_mapping.items()
            if article in general_articles
        )
        
        if general_relations > 0:
            quality_issues.append(f"发现{general_relations}个总则条款关联")
            
        # 检查法条覆盖范围
        article_numbers = [int(art) for art in self.article_crime_mapping.keys() if art.isdigit()]
        max_article = max(article_numbers) if article_numbers else 0
        
        if max_article > 451:
            quality_issues.append(f"发现超范围法条: 最大{max_article}条")
            
        # 计算数据分布
        crime_relation_counts = [sum(articles.values()) for articles in self.crime_article_mapping.values()]
        avg_relations_per_crime = sum(crime_relation_counts) / len(crime_relation_counts) if crime_relation_counts else 0
        
        return {
            'quality_issues': quality_issues,
            'article_range': {'min': min(article_numbers) if article_numbers else 0, 'max': max_article},
            'avg_relations_per_crime': round(avg_relations_per_crime, 2),
            'crimes_with_many_articles': len([c for c in crime_relation_counts if c > 20])
        }

    def _get_top_crimes(self, top_k: int) -> List[Tuple[str, int]]:
        """获取最频繁的罪名"""
        crime_counts = {
            crime: sum(articles.values())
            for crime, articles in self.crime_article_mapping.items()
        }
        return sorted(crime_counts.items(), key=lambda x: x[1], reverse=True)[:top_k]

    def _get_top_articles(self, top_k: int) -> List[Tuple[str, int]]:
        """获取最常被引用的法条"""
        article_counts = {
            article: sum(crimes.values())
            for article, crimes in self.article_crime_mapping.items()
        }
        return sorted(article_counts.items(), key=lambda x: x[1], reverse=True)[:top_k]

    def _create_empty_result(self) -> Dict[str, Any]:
        """创建空的结果"""
        return {
            'success': False,
            'total_crimes': 0,
            'total_articles': 0,
            'total_relations': 0,
            'crime_article_mapping': {},
            'article_crime_mapping': {},
            'error': 'Failed to extract relations from case data'
        }
