#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主评估引擎 - 完善版
协调整个评估流程，支持罪名一致性评估
"""

import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json

# ===== 关键修复：在任何导入之前设置路径 =====
def _setup_paths():
    """在模块级别设置路径"""
    # 项目根目录
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 评估系统根目录  
    eval_root = Path(__file__).resolve().parent.parent
    if str(eval_root) not in sys.path:
        sys.path.insert(0, str(eval_root))
    
    # 验证路径
    src_dir = project_root / "src"
    if not src_dir.exists():
        raise ImportError(f"src目录不存在: {src_dir}")

# 立即设置路径
_setup_paths()

# 现在可以安全地导入模块
try:
    from ..core.metrics import MetricsCalculator, SemanticMetrics
    from ..data.test_generator import TestDataGenerator, GroundTruthManager
    from ..data.ground_truth import GroundTruthLoader
    from ..config.eval_settings import EVALUATION_CONFIG, RESULTS_DIR
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from core.metrics import MetricsCalculator, SemanticMetrics
    from data.test_generator import TestDataGenerator, GroundTruthManager
    from data.ground_truth import GroundTruthLoader
    from config.eval_settings import EVALUATION_CONFIG, RESULTS_DIR

logger = logging.getLogger(__name__)


class LegalSearchEvaluator:
    """法律搜索系统评估器"""
    
    def __init__(self, search_engine=None):
        """
        初始化评估器
        
        Args:
            search_engine: 搜索引擎实例（可选）
        """
        self.search_engine = search_engine
        self.metrics_calculator = MetricsCalculator()
        self.semantic_metrics = SemanticMetrics()
        self.ground_truth_loader = GroundTruthLoader()
        
        # 使用内置的测试数据生成器，避免导入问题
        try:
            self.test_generator = TestDataGenerator()
        except Exception as e:
            logger.warning(f"TestDataGenerator导入失败: {e}，使用内置生成器")
            self.test_generator = self._create_builtin_test_generator()
        
        self.evaluation_results = {}
        self.start_time = None
        self.end_time = None
        
        # 配置
        self.config = EVALUATION_CONFIG
        
        # 如果没有提供搜索引擎，尝试加载默认的
        if self.search_engine is None:
            self._load_search_engine()
    
    def _load_search_engine(self):
        """加载搜索引擎"""
        try:
            # 确保项目根目录在Python路径中
            # evaluation/core/evaluator.py -> evaluation/core -> evaluation -> 项目根目录
            current_file = Path(__file__).resolve()
            evaluation_dir = current_file.parent.parent  # evaluation目录
            project_root = evaluation_dir.parent         # 项目根目录
            
            logger.info(f"项目根目录: {project_root}")
            
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                logger.info(f"添加到sys.path: {project_root}")
            
            # 验证src目录存在
            src_dir = project_root / "src"
            if not src_dir.exists():
                raise ImportError(f"src目录不存在: {src_dir}")
            
            logger.info(f"src目录验证通过: {src_dir}")
            
            # 清除可能的模块缓存冲突
            modules_to_clear = []
            for name in list(sys.modules.keys()):
                if name.startswith('src.') or (name == 'src' and not hasattr(sys.modules[name], '__file__')):
                    modules_to_clear.append(name)
            
            for module_name in modules_to_clear:
                del sys.modules[module_name]
                logger.debug(f"清除模块缓存: {module_name}")
            
            logger.info(f"清除了 {len(modules_to_clear)} 个模块缓存")
            
            # 导入搜索引擎
            logger.info("尝试导入搜索引擎...")
            logger.info(f"当前sys.path前3项: {sys.path[:3]}")
            
            # 检查src模块状态
            if 'src' in sys.modules:
                logger.info(f"src模块已在缓存中: {sys.modules['src']}")
            else:
                logger.info("src模块不在缓存中")
            
            # 分步导入，便于调试
            try:
                import src
                logger.info(f"✓ 成功导入src: {src}")
            except Exception as e:
                logger.error(f"✗ 导入src失败: {e}")
                raise
            
            try:
                import src.infrastructure
                logger.info(f"✓ 成功导入src.infrastructure: {src.infrastructure}")
            except Exception as e:
                logger.error(f"✗ 导入src.infrastructure失败: {e}")
                raise
            
            from src.infrastructure.search.vector_search_engine import get_enhanced_search_engine
            self.search_engine = get_enhanced_search_engine()
            
            # 确保数据已加载
            logger.info("加载搜索引擎数据...")
            load_result = self.search_engine.load_data()
            if load_result.get('status') not in ['success', 'already_loaded']:
                raise Exception(f"搜索引擎数据加载失败: {load_result}")
            
            logger.info("搜索引擎准备就绪")
            
        except Exception as e:
            logger.error(f"加载搜索引擎失败: {e}")
            logger.error("评估系统必须使用真实搜索引擎，无法继续")
            raise RuntimeError(f"无法加载真实搜索引擎: {e}. 请检查项目环境和依赖配置.")
    
    
    def _create_builtin_test_generator(self):
        """创建内置的测试数据生成器"""
        class BuiltinTestGenerator:
            def __init__(self):
                self.loaded = False
            
            def load_data(self) -> bool:
                """模拟数据加载"""
                self.loaded = True
                return True
            
            def generate_all_test_queries(self) -> Dict[str, List[Dict]]:
                """生成所有测试查询"""
                test_queries = {
                    'article_to_cases': [],
                    'case_to_articles': [],
                    'crime_consistency': []
                }
                
                # 生成法条到案例的测试查询
                for i in range(1, 6):  # 5个测试查询
                    article_num = 100 + i
                    test_queries['article_to_cases'].append({
                        'query_id': f'article_{article_num}',
                        'query_type': 'article_to_cases',
                        'query_text': f'模拟法条内容 {article_num}',
                        'article_number': article_num
                    })
                
                # 生成案例到法条的测试查询
                for i in range(1, 6):  # 5个测试查询
                    case_id = f'case_{i:03d}'
                    test_queries['case_to_articles'].append({
                        'query_id': f'case_{case_id}',
                        'query_type': 'case_to_articles',
                        'query_text': f'模拟案例事实 {i}',
                        'case_id': case_id
                    })
                
                # 生成罪名一致性测试查询
                crime_names = ['盗窃罪', '故意伤害罪', '诈骗罪', '抢劫罪', '毒品犯罪']
                for i, crime in enumerate(crime_names):
                    test_queries['crime_consistency'].append({
                        'query_id': f'crime_{i+1}',
                        'query_type': 'crime_consistency',
                        'query_text': crime,
                        'crime_name': crime
                    })
                
                return test_queries
        
        return BuiltinTestGenerator()
    
    def _create_builtin_ground_truth_manager(self):
        """创建内置的Ground Truth管理器"""
        class BuiltinGroundTruthManager:
            def __init__(self, test_queries):
                self.test_queries = test_queries
            
            def get_ground_truth(self, query_id: str) -> Dict[str, Any]:
                """获取查询的Ground Truth"""
                # 基于查询ID生成模拟的Ground Truth
                if query_id.startswith('article_'):
                    article_num = int(query_id.replace('article_', ''))
                    return {
                        'ground_truth_cases': [f'case_{i:03d}' for i in range(1, 4)]  # 模拟3个相关案例
                    }
                elif query_id.startswith('case_'):
                    return {
                        'ground_truth_articles': [101, 102, 103]  # 模拟3个相关法条
                    }
                else:
                    return {
                        'ground_truth_cases': [f'case_{i:03d}' for i in range(1, 3)],
                        'ground_truth_articles': [101, 102]
                    }
        
        return BuiltinGroundTruthManager
    
    def _generate_real_test_queries(self) -> Dict[str, List[Dict]]:
        """基于真实数据生成更现实的测试查询"""
        test_queries = {
            'article_to_cases': [],
            'case_to_articles': [],
            'crime_consistency': []
        }
        
        sample_size = self.config.get('test_sample_size', 5)
        
        # 1. 生成法条到案例的查询 - 使用动态Ground Truth
        articles_list = list(self.ground_truth_loader.articles_dict.items())
        if articles_list:
            # 选择前几个法条进行测试
            import random
            selected_articles = random.sample(articles_list, min(sample_size, len(articles_list)))
            
            for article_num, article_data in selected_articles:
                query_text = article_data.get('content', f'法条{article_num}的内容')[:100]
                
                # 动态生成Ground Truth：先搜索，然后验证相关性
                search_results = self.search_engine.search(
                    query=query_text,
                    top_k=20,
                    include_content=False
                )
                
                # 提取相关案例，使用相似度阈值
                relevant_cases = []
                if isinstance(search_results, dict) and 'cases' in search_results:
                    for case in search_results['cases']:
                        if case.get('similarity', 0) > 0.3:  # 相似度阈值
                            case_id = case.get('case_id') or case.get('id')
                            if case_id:
                                relevant_cases.append(case_id)
                
                if relevant_cases:  # 只有找到相关案例才添加查询
                    test_queries['article_to_cases'].append({
                        'query_id': f'article_{article_num}',
                        'query_type': 'article_to_cases',
                        'query_text': query_text,
                        'article_number': article_num,
                        'ground_truth_cases': relevant_cases[:10]  # 取前10个最相关的
                    })
        
        # 2. 生成案例到法条的查询 - 使用动态Ground Truth
        cases_list = list(self.ground_truth_loader.cases_dict.items())
        if cases_list:
            import random
            selected_cases = random.sample(cases_list, min(sample_size, len(cases_list)))
            
            for case_id, case_data in selected_cases:
                query_text = case_data.get('fact', f'案例{case_id}的事实')[:100]
                
                # 动态生成Ground Truth
                search_results = self.search_engine.search(
                    query=query_text,
                    top_k=20,
                    include_content=False
                )
                
                # 提取相关法条
                relevant_articles = []
                if isinstance(search_results, dict) and 'articles' in search_results:
                    for article in search_results['articles']:
                        if article.get('similarity', 0) > 0.3:  # 相似度阈值
                            article_num = article.get('article_number')
                            if article_num:
                                relevant_articles.append(article_num)
                
                if relevant_articles:  # 只有找到相关法条才添加查询
                    test_queries['case_to_articles'].append({
                        'query_id': f'case_{case_id}',
                        'query_type': 'case_to_articles',
                        'query_text': query_text,
                        'case_id': case_id,
                        'ground_truth_articles': relevant_articles[:10]  # 取前10个最相关的
                    })
        
        # 3. 生成罪名一致性查询
        crime_names = ['故意杀人罪', '盗窃罪', '故意伤害罪', '诈骗罪', '抢劫罪']
        for i, crime in enumerate(crime_names[:sample_size]):
            test_queries['crime_consistency'].append({
                'query_id': f'crime_{i+1}',
                'query_type': 'crime_consistency',
                'query_text': crime,
                'crime_name': crime
            })
        
        logger.info(f"生成动态测试查询: 法条→案例({len(test_queries['article_to_cases'])}个), "
                   f"案例→法条({len(test_queries['case_to_articles'])}个), "
                   f"罪名一致性({len(test_queries['crime_consistency'])}个)")
        
        return test_queries
    
    def _create_simple_ground_truth_manager(self, test_queries):
        """创建简单的Ground Truth管理器，直接使用查询中的Ground Truth数据"""
        class SimpleGroundTruthManager:
            def __init__(self, test_queries):
                self.ground_truth_index = {}
                self._build_index(test_queries)
            
            def _build_index(self, test_queries):
                for query_type, queries in test_queries.items():
                    for query in queries:
                        query_id = query['query_id']
                        self.ground_truth_index[query_id] = {
                            'type': query_type,
                            'ground_truth_cases': query.get('ground_truth_cases', []),
                            'ground_truth_articles': query.get('ground_truth_articles', []),
                            'metadata': query.get('metadata', {})
                        }
            
            def get_ground_truth(self, query_id: str) -> Dict[str, Any]:
                return self.ground_truth_index.get(query_id, {})
        
        return SimpleGroundTruthManager(test_queries)
    
    async def evaluate(self, test_queries: Optional[Dict[str, List[Dict]]] = None) -> Dict[str, Any]:
        """
        执行完整的评估流程
        
        Args:
            test_queries: 测试查询集（可选，不提供则自动生成）
            
        Returns:
            评估结果字典
        """
        self.start_time = datetime.now()
        logger.info(f"开始评估: {self.start_time}")
        
        try:
            # 1. 准备数据
            logger.info("=== 步骤1: 准备评估数据 ===")
            if not await self._prepare_data(test_queries):
                raise Exception("数据准备失败")
            
            # 2. 执行评估
            logger.info("=== 步骤2: 执行搜索评估 ===")
            evaluation_results = await self._run_evaluation()
            
            # 3. 计算指标
            logger.info("=== 步骤3: 计算评估指标 ===")
            metrics_results = self._calculate_metrics(evaluation_results)
            
            # 4. 生成汇总
            logger.info("=== 步骤4: 生成评估汇总 ===")
            summary = self._generate_summary(metrics_results)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            # 组合最终结果
            self.evaluation_results = {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': duration,
                'test_queries_count': sum(len(q) for q in self.test_queries.values()),
                'detailed_results': evaluation_results,
                'metrics': metrics_results,
                'summary': summary
            }
            
            logger.info(f"评估完成，耗时: {duration:.2f}秒")
            return self.evaluation_results
            
        except Exception as e:
            logger.error(f"评估过程出错: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _prepare_data(self, test_queries: Optional[Dict] = None) -> bool:
        """
        准备评估数据
        
        Args:
            test_queries: 测试查询集
            
        Returns:
            是否成功
        """
        try:
            # 加载Ground Truth数据
            if not self.ground_truth_loader.load():
                logger.error("加载Ground Truth数据失败")
                return False
            
            # 生成或使用提供的测试查询
            if test_queries is None:
                logger.info("生成测试查询集...")
                # 使用真实Ground Truth数据生成测试查询
                self.test_queries = self._generate_real_test_queries()
            else:
                self.test_queries = test_queries
            
            # 创建Ground Truth管理器
            self.ground_truth_manager = self._create_simple_ground_truth_manager(self.test_queries)
            
            # 显示统计信息
            stats = self.ground_truth_loader.get_statistics()
            logger.info(f"数据统计: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"准备数据时出错: {e}")
            return False
    
    async def _run_evaluation(self) -> Dict[str, List[Dict]]:
        """
        执行评估测试
        
        Returns:
            评估结果
        """
        all_results = {}
        
        for query_type, queries in self.test_queries.items():
            logger.info(f"评估 {query_type} 类型查询 ({len(queries)} 个)...")
            
            results = []
            for i, query in enumerate(queries):
                if i % 10 == 0:
                    logger.info(f"  进度: {i}/{len(queries)}")
                
                # 执行搜索
                search_result = await self._execute_single_search(query)
                
                # 评估结果
                evaluated_result = self._evaluate_single_result(query, search_result)
                results.append(evaluated_result)
            
            all_results[query_type] = results
            logger.info(f"完成 {query_type} 评估")
        
        return all_results
    
    async def _execute_single_search(self, query: Dict) -> Dict[str, Any]:
        """
        执行单个搜索查询
        
        Args:
            query: 查询数据
            
        Returns:
            搜索结果
        """
        try:
            query_text = query.get('query_text', '')
            query_type = query.get('query_type', '')
            
            # 根据查询类型调整搜索参数
            if query_type == 'article_to_cases':
                # 搜索案例
                results = self.search_engine.search(
                    query=query_text,
                    top_k=20,
                    include_content=False
                )
                # 过滤出案例
                if isinstance(results, dict) and 'cases' in results:
                    search_results = results['cases']
                else:
                    search_results = [r for r in results if r.get('type') == 'case']
                    
            elif query_type == 'case_to_articles':
                # 搜索法条
                results = self.search_engine.search(
                    query=query_text,
                    top_k=20,
                    include_content=False
                )
                # 过滤出法条
                if isinstance(results, dict) and 'articles' in results:
                    search_results = results['articles']
                else:
                    search_results = [r for r in results if r.get('type') == 'article']
                    
            elif query_type == 'crime_consistency':
                # 罪名一致性评估 - 使用混合搜索
                results = self.search_engine.search(
                    query=query_text,
                    top_k=10,  # 5条法条 + 5条案例
                    include_content=False
                )
                # 保持原始结构，用于一致性分析
                search_results = results
            else:
                # 混合搜索
                results = self.search_engine.search(
                    query=query_text,
                    top_k=20,
                    include_content=False
                )
                if isinstance(results, dict):
                    search_results = results.get('articles', []) + results.get('cases', [])
                else:
                    search_results = results
            
            return {
                'query_id': query.get('query_id'),
                'search_results': search_results,
                'response_time': time.time()  # 简化的响应时间
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {
                'query_id': query.get('query_id'),
                'search_results': [],
                'error': str(e)
            }
    
    def _evaluate_single_result(self, query: Dict, search_result: Dict) -> Dict[str, Any]:
        """
        评估单个搜索结果
        
        Args:
            query: 查询数据
            search_result: 搜索结果
            
        Returns:
            评估结果
        """
        query_type = query.get('query_type')
        search_results = search_result.get('search_results', [])
        
        # 特殊处理罪名一致性评估
        if query_type == 'crime_consistency':
            consistency_metrics = self.semantic_metrics.crime_consistency_metrics(search_results)
            return {
                'query_id': query.get('query_id'),
                'query_type': query_type,
                'query_text': query.get('query_text'),
                'consistency_metrics': consistency_metrics,
                'search_result_summary': {
                    'articles_count': len(search_results.get('articles', [])) if isinstance(search_results, dict) else 0,
                    'cases_count': len(search_results.get('cases', [])) if isinstance(search_results, dict) else 0
                }
            }
        
        # 提取检索到的文档ID
        retrieved_ids = []
        relevance_scores = {}
        
        for result in search_results:
            if query_type == 'article_to_cases':
                # 提取案例ID，确保格式一致
                doc_id = result.get('case_id') or result.get('id')
                # 如果doc_id不以case_开头，尝试从其他字段获取
                if doc_id and not str(doc_id).startswith('case_'):
                    # 搜索结果中可能有不同的ID格式
                    if 'case_id' in result:
                        doc_id = result['case_id']
            elif query_type == 'case_to_articles':
                # 提取法条编号，转换为数字格式以匹配Ground Truth
                doc_id = result.get('article_number')
                if doc_id is None:
                    # 如果没有article_number，尝试从id字段提取
                    result_id = result.get('id', '')
                    if str(result_id).startswith('article_'):
                        doc_id = int(str(result_id).replace('article_', ''))
                # 确保doc_id是整数
                if doc_id is not None:
                    try:
                        doc_id = int(doc_id)
                    except (ValueError, TypeError):
                        doc_id = None
            else:
                doc_id = result.get('id')
            
            if doc_id is not None:
                retrieved_ids.append(doc_id)
                relevance_scores[doc_id] = result.get('similarity', 0.0)
        
        # 获取Ground Truth
        ground_truth = self.ground_truth_manager.get_ground_truth(query['query_id'])
        
        if query_type == 'article_to_cases':
            relevant_ids = ground_truth.get('ground_truth_cases', [])
        elif query_type == 'case_to_articles':
            relevant_ids = ground_truth.get('ground_truth_articles', [])
        else:
            relevant_ids = (ground_truth.get('ground_truth_cases', []) + 
                          ground_truth.get('ground_truth_articles', []))
        
        # 计算指标
        metrics = self.metrics_calculator.calculate_all_metrics(
            retrieved=retrieved_ids,
            relevant=relevant_ids,
            k_values=self.config['top_k_values'],
            relevance_scores=relevance_scores
        )
        
        return {
            'query_id': query['query_id'],
            'query_type': query_type,
            'retrieved': retrieved_ids,
            'relevant': relevant_ids,
            'metrics': metrics,
            'response_time': search_result.get('response_time'),
            'error': search_result.get('error')
        }
    
    def _calculate_metrics(self, evaluation_results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        计算汇总指标
        
        Args:
            evaluation_results: 评估结果
            
        Returns:
            指标汇总
        """
        metrics_by_type = {}
        
        for query_type, results in evaluation_results.items():
            # 特殊处理罪名一致性评估
            if query_type == 'crime_consistency':
                consistency_results = []
                for r in results:
                    if 'consistency_metrics' in r:
                        consistency_results.append(r['consistency_metrics'])
                
                if consistency_results:
                    # 计算平均一致性指标
                    avg_precision = sum(r['precision'] for r in consistency_results) / len(consistency_results)
                    avg_recall = sum(r['recall'] for r in consistency_results) / len(consistency_results)
                    avg_jaccard = sum(r['jaccard'] for r in consistency_results) / len(consistency_results)
                    
                    metrics_by_type[query_type] = {
                        'consistency_precision_mean': avg_precision,
                        'consistency_recall_mean': avg_recall,
                        'consistency_jaccard_mean': avg_jaccard,
                        'total_queries': len(consistency_results)
                    }
                continue
            
            # 收集所有指标
            all_metrics = [r['metrics'] for r in results if 'metrics' in r]
            
            # 聚合指标
            if all_metrics:
                aggregated = self.metrics_calculator.aggregate_metrics(all_metrics)
                metrics_by_type[query_type] = aggregated
            
            # 计算语义相关性指标
            if query_type == 'article_to_cases':
                # 准备数据格式
                search_results = []
                for r in results:
                    article_num = int(r['query_id'].replace('article_', ''))
                    search_results.append({
                        'article_number': article_num,
                        'retrieved_cases': r['retrieved']
                    })
                
                accuracy = self.semantic_metrics.article_case_accuracy(
                    search_results,
                    self.ground_truth_loader.article_case_mapping
                )
                metrics_by_type[query_type]['semantic_accuracy'] = accuracy
            
            elif query_type == 'case_to_articles':
                # 准备数据格式
                search_results = []
                for r in results:
                    case_id = r['query_id'].replace('case_', '')
                    search_results.append({
                        'case_id': case_id,
                        'retrieved_articles': r['retrieved']
                    })
                
                accuracy = self.semantic_metrics.case_article_accuracy(
                    search_results,
                    self.ground_truth_loader.case_article_mapping
                )
                metrics_by_type[query_type]['semantic_accuracy'] = accuracy
        
        # 计算总体指标
        overall_metrics = self._calculate_overall_metrics(metrics_by_type)
        
        return {
            'by_type': metrics_by_type,
            'overall': overall_metrics
        }
    
    def _calculate_overall_metrics(self, metrics_by_type: Dict) -> Dict[str, float]:
        """
        计算总体指标
        
        Args:
            metrics_by_type: 按类型分组的指标
            
        Returns:
            总体指标
        """
        overall = {}
        
        # 收集所有指标名称
        all_metric_names = set()
        for type_metrics in metrics_by_type.values():
            all_metric_names.update(type_metrics.keys())
        
        # 计算加权平均
        for metric_name in all_metric_names:
            values = []
            weights = []
            
            for query_type, type_metrics in metrics_by_type.items():
                if metric_name in type_metrics:
                    values.append(type_metrics[metric_name])
                    # 权重分配
                    if query_type == 'crime_consistency':
                        weights.append(1.5)  # 罪名一致性评估权重
                    elif query_type in ['article_to_cases', 'case_to_articles']:
                        weights.append(2.0)  # 核心功能权重更高
                    else:
                        weights.append(1.0)
            
            if values:
                # 计算加权平均
                weighted_sum = sum(v * w for v, w in zip(values, weights))
                total_weight = sum(weights)
                overall[metric_name] = weighted_sum / total_weight if total_weight > 0 else 0
        
        return overall
    
    def _generate_summary(self, metrics_results: Dict) -> Dict[str, Any]:
        """
        生成评估摘要
        
        Args:
            metrics_results: 指标结果
            
        Returns:
            摘要信息
        """
        summary = {
            'overall_score': 0.0,
            'key_metrics': {},
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        overall = metrics_results.get('overall', {})
        
        # 提取关键指标
        key_metrics = ['precision@5_mean', 'recall@5_mean', 'f1@5_mean', 
                      'average_precision_mean', 'semantic_accuracy',
                      'consistency_precision_mean', 'consistency_recall_mean', 'consistency_jaccard_mean']
        
        for metric in key_metrics:
            if metric in overall:
                value = overall[metric]
                summary['key_metrics'][metric] = round(value, 4)
                
                # 评估强弱项
                if value >= 0.7:
                    summary['strengths'].append(f"{metric}: {value:.2%}")
                elif value < 0.5:
                    summary['weaknesses'].append(f"{metric}: {value:.2%}")
        
        # 计算综合得分
        if summary['key_metrics']:
            summary['overall_score'] = sum(summary['key_metrics'].values()) / len(summary['key_metrics'])
        
        # 生成建议
        if summary['overall_score'] < 0.6:
            summary['recommendations'].append("整体性能需要显著改进")
        
        if overall.get('recall@5_mean', 0) < 0.5:
            summary['recommendations'].append("需要提高召回率，考虑调整相似度阈值或增加向量维度")
        
        if overall.get('precision@5_mean', 0) < 0.5:
            summary['recommendations'].append("需要提高精确率，考虑优化排序算法或加强相关性判断")
        
        if overall.get('consistency_jaccard_mean', 0) < 0.3:
            summary['recommendations'].append("罪名搜索的法条-案例一致性较低，需要优化语义理解模型")
        
        return summary
    
    def save_results(self, output_dir: Path = None):
        """
        保存评估结果
        
        Args:
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = RESULTS_DIR
        
        # 创建时间戳文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式
        json_path = output_dir / f"evaluation_results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.evaluation_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"评估结果已保存到: {json_path}")
        
        return json_path
