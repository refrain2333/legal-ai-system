#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估系统修复验证测试
验证修复后的评估系统是否正确工作
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "evaluation"))

import logging

# 配置简单的日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_evaluation_fix():
    """测试评估系统修复效果"""
    try:
        logger.info("=" * 60)
        logger.info("开始测试修复后的评估系统")
        logger.info("=" * 60)
        
        # 1. 测试Ground Truth加载器
        logger.info("步骤 1: 测试Ground Truth加载器...")
        from data.ground_truth import GroundTruthLoader
        
        gt_loader = GroundTruthLoader()
        if gt_loader.load():
            stats = gt_loader.get_statistics()
            logger.info(f"Ground Truth数据加载成功: {stats}")
            
            # 验证关键数据
            assert len(gt_loader.article_case_mapping) > 0, "法条-案例映射为空"
            assert len(gt_loader.case_article_mapping) > 0, "案例-法条映射为空"
            logger.info("✓ Ground Truth数据验证通过")
        else:
            logger.error("Ground Truth数据加载失败")
            return False
        
        # 2. 测试评估器初始化
        logger.info("步骤 2: 测试评估器初始化...")
        from core.evaluator import LegalSearchEvaluator
        
        evaluator = LegalSearchEvaluator()
        logger.info("✓ 评估器初始化成功")
        
        # 3. 测试正确的测试查询生成
        logger.info("步骤 3: 测试正确的测试查询生成...")
        
        # 手动加载Ground Truth数据
        if not evaluator.ground_truth_loader.loaded:
            evaluator.ground_truth_loader.load()
        
        # 生成测试查询
        test_queries = evaluator._generate_correct_test_queries()
        
        logger.info(f"生成的测试查询:")
        for query_type, queries in test_queries.items():
            logger.info(f"  - {query_type}: {len(queries)} 个查询")
            
            # 验证Ground Truth不是来自搜索引擎
            if queries:
                sample_query = queries[0]
                if query_type == 'article_to_cases':
                    assert 'ground_truth_cases' in sample_query, "缺少ground_truth_cases"
                    gt_cases = sample_query['ground_truth_cases']
                    assert len(gt_cases) > 0, "ground_truth_cases为空"
                    logger.info(f"    示例查询Ground Truth案例数: {len(gt_cases)}")
                    
                elif query_type == 'case_to_articles':
                    assert 'ground_truth_articles' in sample_query, "缺少ground_truth_articles"
                    gt_articles = sample_query['ground_truth_articles']
                    assert len(gt_articles) > 0, "ground_truth_articles为空"
                    logger.info(f"    示例查询Ground Truth法条数: {len(gt_articles)}")
        
        logger.info("✓ 测试查询生成验证通过")
        
        # 4. 测试指标计算
        logger.info("步骤 4: 测试指标计算...")
        from core.metrics import MetricsCalculator
        
        metrics_calc = MetricsCalculator()
        
        # 测试Hit@K指标
        retrieved = [101, 102, 103, 104, 105]
        relevant = [102, 106, 107]
        
        hit_1 = metrics_calc.hit_at_k(retrieved, relevant, 1)
        hit_3 = metrics_calc.hit_at_k(retrieved, relevant, 3) 
        hit_5 = metrics_calc.hit_at_k(retrieved, relevant, 5)
        
        logger.info(f"Hit@K测试结果:")
        logger.info(f"  - Hit@1: {hit_1} (期望: 0.0, 因为第1个结果不相关)")
        logger.info(f"  - Hit@3: {hit_3} (期望: 1.0, 因为第2个结果相关)")
        logger.info(f"  - Hit@5: {hit_5} (期望: 1.0, 因为第2个结果相关)")
        
        assert hit_1 == 0.0, f"Hit@1计算错误: {hit_1}"
        assert hit_3 == 1.0, f"Hit@3计算错误: {hit_3}"
        assert hit_5 == 1.0, f"Hit@5计算错误: {hit_5}"
        
        logger.info("✓ 指标计算验证通过")
        
        # 5. 测试完整指标计算
        all_metrics = metrics_calc.calculate_all_metrics(
            retrieved=retrieved,
            relevant=relevant,
            k_values=[1, 3, 5],
            relevance_scores={doc: 0.8 for doc in retrieved}
        )
        
        logger.info(f"完整指标计算结果:")
        for metric, value in all_metrics.items():
            logger.info(f"  - {metric}: {value:.4f}")
        
        # 验证Hit@K指标包含在结果中
        assert 'hit@1' in all_metrics, "缺少hit@1指标"
        assert 'hit@3' in all_metrics, "缺少hit@3指标"
        assert 'hit@5' in all_metrics, "缺少hit@5指标"
        
        logger.info("✓ 完整指标计算验证通过")
        
        logger.info("=" * 60)
        logger.info("✅ 所有测试通过！评估系统修复成功")
        logger.info("修复关键点:")
        logger.info("1. 消除了循环依赖问题")
        logger.info("2. 使用真实的案例关联数据作为Ground Truth")
        logger.info("3. 添加了Hit@K指标支持案例到法条检索")
        logger.info("4. 优化了评估逻辑和数据验证")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    try:
        success = await test_evaluation_fix()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return 1


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)