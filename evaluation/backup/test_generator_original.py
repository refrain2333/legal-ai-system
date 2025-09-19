#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据生成器
从真实数据中生成评估测试用例
"""

import pickle
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, config_path: Path = None):
        """
        初始化测试数据生成器
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            from ..config.eval_settings import (
                ARTICLE_CASE_MAPPINGS_PATH,
                CRIMINAL_ARTICLES_PATH,
                CRIMINAL_CASES_PATH,
                CRIME_TYPES_PATH,
                EVALUATION_CONFIG
            )
            self.mappings_path = ARTICLE_CASE_MAPPINGS_PATH
            self.articles_path = CRIMINAL_ARTICLES_PATH
            self.cases_path = CRIMINAL_CASES_PATH
            self.crimes_path = CRIME_TYPES_PATH
            self.config = EVALUATION_CONFIG
        
        self.article_case_mapping = None
        self.case_article_mapping = None
        self.articles_data = None
        self.cases_data = None
        self.crime_keywords = None
        
        # 设置随机种子
        random.seed(self.config.get('random_seed', 42))
    
    def load_data(self) -> bool:
        """
        加载所有必要的数据
        
        Returns:
            是否成功加载
        """
        try:
            # 导入模块适配器
            from .ground_truth import _module_adapter
            
            # 创建临时假模块用于pickle加载
            _module_adapter.create_fake_modules_if_needed()
            
            try:
                # 加载法条-案例映射
                logger.info("加载法条-案例映射数据...")
                with open(self.mappings_path, 'rb') as f:
                    self.article_case_mapping = pickle.load(f)
                
                # 加载法条数据
                logger.info("加载法条数据...")
                with open(self.articles_path, 'rb') as f:
                    self.articles_data = pickle.load(f)
                
                # 加载案例数据
                logger.info("加载案例数据...")
                with open(self.cases_path, 'rb') as f:
                    self.cases_data = pickle.load(f)
            finally:
                # 清理临时假模块
                _module_adapter.cleanup_fake_modules()
            
            # 加载罪名关键词
            logger.info("加载罪名关键词...")
            if self.crimes_path.exists():
                with open(self.crimes_path, 'r', encoding='utf-8') as f:
                    self.crime_keywords = [line.strip() for line in f if line.strip()]
            
            # 构建反向映射（案例到法条）
            self._build_case_article_mapping()
            
            logger.info(f"数据加载完成: {len(self.articles_data)}条法条, "
                       f"{len(self.cases_data)}个案例, "
                       f"{len(self.crime_keywords) if self.crime_keywords else 0}个罪名")
            
            return True
            
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return False
    
    def _build_case_article_mapping(self):
        """构建案例到法条的反向映射"""
        self.case_article_mapping = {}
        
        # 从案例数据中提取映射关系
        for case in self.cases_data:
            case_id = case.get('case_id', case.get('id'))
            relevant_articles = case.get('relevant_articles', [])
            if case_id and relevant_articles:
                self.case_article_mapping[case_id] = relevant_articles
    
    def generate_article_to_case_queries(self, sample_size: int = None) -> List[Dict[str, Any]]:
        """
        生成法条到案例的测试查询
        
        Args:
            sample_size: 样本数量
            
        Returns:
            测试查询列表
        """
        if sample_size is None:
            sample_size = self.config.get('test_sample_size', 100)
        
        test_queries = []
        
        # 选择有映射关系的法条
        articles_with_cases = [
            article_num for article_num in self.article_case_mapping
            if self.article_case_mapping[article_num]
        ]
        
        # 随机采样
        sampled_articles = random.sample(
            articles_with_cases,
            min(sample_size, len(articles_with_cases))
        )
        
        for article_num in sampled_articles:
            # 找到对应的法条内容
            article_data = None
            for article in self.articles_data:
                if article.get('article_number') == article_num:
                    article_data = article
                    break
            
            if article_data:
                test_query = {
                    'query_id': f'article_{article_num}',
                    'query_type': 'article_to_cases',
                    'query_text': article_data.get('content', ''),
                    'article_number': article_num,
                    'ground_truth_cases': self.article_case_mapping[article_num],
                    'metadata': {
                        'title': article_data.get('title', ''),
                        'chapter': article_data.get('chapter', '')
                    }
                }
                test_queries.append(test_query)
        
        logger.info(f"生成了 {len(test_queries)} 个法条到案例的测试查询")
        return test_queries
    
    def generate_case_to_article_queries(self, sample_size: int = None) -> List[Dict[str, Any]]:
        """
        生成案例到法条的测试查询
        
        Args:
            sample_size: 样本数量
            
        Returns:
            测试查询列表
        """
        if sample_size is None:
            sample_size = self.config.get('test_sample_size', 100)
        
        test_queries = []
        
        # 选择有法条引用的案例
        cases_with_articles = [
            case for case in self.cases_data
            if case.get('relevant_articles')
        ]
        
        # 随机采样
        sampled_cases = random.sample(
            cases_with_articles,
            min(sample_size, len(cases_with_articles))
        )
        
        for case in sampled_cases:
            case_id = case.get('case_id', case.get('id'))
            test_query = {
                'query_id': f'case_{case_id}',
                'query_type': 'case_to_articles',
                'query_text': case.get('fact', ''),
                'case_id': case_id,
                'ground_truth_articles': case.get('relevant_articles', []),
                'metadata': {
                    'accusations': case.get('accusations', []),
                    'criminals': case.get('criminals', [])
                }
            }
            test_queries.append(test_query)
        
        logger.info(f"生成了 {len(test_queries)} 个案例到法条的测试查询")
        return test_queries
    
    def generate_crime_keyword_queries(self, sample_size: int = None) -> List[Dict[str, Any]]:
        """
        生成罪名关键词测试查询
        
        Args:
            sample_size: 样本数量
            
        Returns:
            测试查询列表
        """
        if sample_size is None:
            sample_size = self.config.get('test_sample_size', 50)
        
        if not self.crime_keywords:
            logger.warning("没有加载罪名关键词数据")
            return []
        
        test_queries = []
        
        # 随机采样罪名
        sampled_crimes = random.sample(
            self.crime_keywords,
            min(sample_size, len(self.crime_keywords))
        )
        
        for crime in sampled_crimes:
            # 找到包含该罪名的案例
            relevant_cases = []
            for case in self.cases_data:
                accusations = case.get('accusations', [])
                if any(crime in acc for acc in accusations):
                    case_id = case.get('case_id', case.get('id'))
                    relevant_cases.append(case_id)
            
            # 找到相关的法条
            relevant_articles = []
            for article in self.articles_data:
                crime_types = article.get('crime_types', [])
                content = article.get('content', '')
                if crime in content or any(crime in ct for ct in crime_types):
                    article_num = article.get('article_number')
                    relevant_articles.append(article_num)
            
            test_query = {
                'query_id': f'crime_{crime}',
                'query_type': 'crime_keyword',
                'query_text': crime,
                'query_crime': crime,
                'ground_truth_cases': relevant_cases[:20],  # 限制数量
                'ground_truth_articles': relevant_articles,
                'metadata': {
                    'total_relevant_cases': len(relevant_cases),
                    'total_relevant_articles': len(relevant_articles)
                }
            }
            test_queries.append(test_query)
        
        logger.info(f"生成了 {len(test_queries)} 个罪名关键词测试查询")
        return test_queries
    
    def generate_mixed_queries(self, sample_size: int = None) -> List[Dict[str, Any]]:
        """
        生成混合测试查询
        
        Args:
            sample_size: 样本数量
            
        Returns:
            测试查询列表
        """
        if sample_size is None:
            sample_size = self.config.get('test_sample_size', 50)
        
        test_queries = []
        
        # 组合不同类型的查询
        queries_per_type = sample_size // 3
        
        # 从案例中提取关键词组合
        for _ in range(queries_per_type):
            case = random.choice(self.cases_data)
            fact = case.get('fact', '')
            
            # 提取关键词（简单方法：取前50个字符）
            query_text = fact[:100] if len(fact) > 100 else fact
            
            case_id = case.get('case_id', case.get('id'))
            test_query = {
                'query_id': f'mixed_case_{case_id}',
                'query_type': 'mixed',
                'query_text': query_text,
                'ground_truth_articles': case.get('relevant_articles', []),
                'ground_truth_cases': [case_id],
                'metadata': {
                    'source': 'case_excerpt'
                }
            }
            test_queries.append(test_query)
        
        logger.info(f"生成了 {len(test_queries)} 个混合测试查询")
        return test_queries
    
    def generate_all_test_queries(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成所有类型的测试查询
        
        Returns:
            按类型分组的测试查询字典
        """
        if not self.articles_data:
            self.load_data()
        
        all_queries = {
            'article_to_cases': self.generate_article_to_case_queries(),
            'case_to_articles': self.generate_case_to_article_queries(),
            'crime_keywords': self.generate_crime_keyword_queries(),
            'mixed': self.generate_mixed_queries()
        }
        
        total_queries = sum(len(queries) for queries in all_queries.values())
        logger.info(f"总共生成了 {total_queries} 个测试查询")
        
        return all_queries
    
    def save_test_queries(self, queries: Dict[str, List[Dict[str, Any]]], 
                         output_path: Path = None):
        """
        保存测试查询到文件
        
        Args:
            queries: 测试查询字典
            output_path: 输出路径
        """
        if output_path is None:
            from ..config.eval_settings import RESULTS_DIR
            output_path = RESULTS_DIR / 'test_queries.pkl'
        
        with open(output_path, 'wb') as f:
            pickle.dump(queries, f)
        
        logger.info(f"测试查询已保存到: {output_path}")


class GroundTruthManager:
    """Ground Truth数据管理器"""
    
    def __init__(self, test_queries: Dict[str, List[Dict[str, Any]]]):
        """
        初始化Ground Truth管理器
        
        Args:
            test_queries: 测试查询字典
        """
        self.test_queries = test_queries
        self.ground_truth_index = {}
        self._build_index()
    
    def _build_index(self):
        """构建Ground Truth索引"""
        for query_type, queries in self.test_queries.items():
            for query in queries:
                query_id = query['query_id']
                self.ground_truth_index[query_id] = {
                    'type': query_type,
                    'ground_truth_cases': query.get('ground_truth_cases', []),
                    'ground_truth_articles': query.get('ground_truth_articles', []),
                    'metadata': query.get('metadata', {})
                }
    
    def get_ground_truth(self, query_id: str) -> Dict[str, Any]:
        """
        获取指定查询的Ground Truth
        
        Args:
            query_id: 查询ID
            
        Returns:
            Ground Truth数据
        """
        return self.ground_truth_index.get(query_id, {})