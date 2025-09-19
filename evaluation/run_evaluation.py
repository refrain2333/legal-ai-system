#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律搜索系统评估主程序
执行完整的评估流程并生成报告
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import argparse
import json

# 设置路径
project_root = Path(__file__).resolve().parent.parent  # 法律项目根目录
evaluation_root = Path(__file__).resolve().parent     # evaluation目录

# 添加两个路径到sys.path
sys.path.insert(0, str(project_root))      # 用于导入src模块
sys.path.insert(0, str(evaluation_root))   # 用于导入evaluation模块

from core.evaluator import LegalSearchEvaluator
from reports.reporter import EvaluationReporter
from config.eval_settings import RESULTS_DIR, LOGGING_CONFIG

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 减少第三方库的日志噪音
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def run_evaluation(args):
    """
    运行评估流程
    
    Args:
        args: 命令行参数
    """
    logger.info("=" * 80)
    logger.info("法律搜索系统评估开始")
    logger.info("=" * 80)
    
    try:
        # 1. 创建评估器
        logger.info("步骤 1/4: 初始化评估器...")
        evaluator = LegalSearchEvaluator()
        
        # 2. 配置评估参数
        if args.test_size:
            from config import eval_settings
            eval_settings.EVALUATION_CONFIG['test_sample_size'] = args.test_size
            logger.info(f"设置测试样本大小: {args.test_size}")
        
        # 3. 执行评估
        logger.info("步骤 2/4: 执行评估测试...")
        results = await evaluator.evaluate()
        
        # 4. 保存原始结果
        logger.info("步骤 3/4: 保存评估结果...")
        json_path = evaluator.save_results()
        
        # 5. 生成报告
        logger.info("步骤 4/4: 生成评估报告...")
        reporter = EvaluationReporter(results)
        
        # 生成文本报告
        text_report_path = reporter.save_text_report()
        
        # 生成JSON报告
        json_report_path = reporter.save_json_report()
        
        # 打印摘要
        print_summary(results)
        
        logger.info("=" * 80)
        logger.info("评估完成!")
        logger.info(f"结果文件: {json_path}")
        logger.info(f"文本报告: {text_report_path}")
        logger.info(f"JSON报告: {json_report_path}")
        logger.info("=" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"评估过程出错: {e}")
        import traceback
        traceback.print_exc()
        raise


def print_summary(results):
    """
    打印评估摘要
    
    Args:
        results: 评估结果
    """
    summary = results.get('summary', {})
    
    print("\n" + "=" * 60)
    print("评估摘要")
    print("=" * 60)
    
    # 综合得分
    overall_score = summary.get('overall_score', 0)
    print(f"\n综合得分: {overall_score:.2%}")
    
    # 评级
    if overall_score >= 0.8:
        rating = "优秀 ⭐⭐⭐⭐⭐"
    elif overall_score >= 0.7:
        rating = "良好 ⭐⭐⭐⭐"
    elif overall_score >= 0.6:
        rating = "合格 ⭐⭐⭐"
    elif overall_score >= 0.5:
        rating = "待改进 ⭐⭐"
    else:
        rating = "需优化 ⭐"
    
    print(f"评级: {rating}")
    
    # 关键指标
    print("\n关键指标:")
    key_metrics = summary.get('key_metrics', {})
    for metric, value in key_metrics.items():
        print(f"  - {metric}: {value:.4f}")
    
    # 优势
    strengths = summary.get('strengths', [])
    if strengths:
        print("\n优势:")
        for strength in strengths[:3]:  # 只显示前3个
            print(f"  ✓ {strength}")
    
    # 待改进
    weaknesses = summary.get('weaknesses', [])
    if weaknesses:
        print("\n待改进:")
        for weakness in weaknesses[:3]:  # 只显示前3个
            print(f"  ✗ {weakness}")
    
    # 建议
    recommendations = summary.get('recommendations', [])
    if recommendations:
        print("\n改进建议:")
        for i, rec in enumerate(recommendations[:3], 1):  # 只显示前3个
            print(f"  {i}. {rec}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='法律搜索系统评估工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_evaluation.py                    # 使用默认设置运行评估
  python run_evaluation.py --test-size 50     # 使用50个测试样本
  python run_evaluation.py --quick             # 快速评估模式
  python run_evaluation.py --verbose          # 显示详细日志
        """
    )
    
    parser.add_argument(
        '--test-size',
        type=int,
        default=None,
        help='每类测试样本数量 (默认: 100)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速评估模式 (使用较少的测试样本)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='输出目录路径'
    )
    
    args = parser.parse_args()
    
    # 快速模式设置
    if args.quick:
        args.test_size = 20
        logger.info("启用快速评估模式 (20个样本)")
    
    # 详细日志设置
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("启用详细日志模式")
    
    # 设置输出目录
    if args.output_dir:
        RESULTS_DIR = args.output_dir
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 运行评估
    try:
        results = asyncio.run(run_evaluation(args))
        
        # 返回成功状态
        return 0 if results.get('summary', {}).get('overall_score', 0) >= 0.6 else 1
        
    except KeyboardInterrupt:
        logger.info("\n评估被用户中断")
        return 2
    except Exception as e:
        logger.error(f"评估失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())