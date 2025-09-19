#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整评估流程的诊断脚本
"""

import sys
import asyncio
from pathlib import Path

def setup_paths():
    """设置路径"""
    project_root = Path(__file__).resolve().parent.parent.parent
    eval_root = Path(__file__).resolve().parent.parent
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(eval_root) not in sys.path:
        sys.path.insert(0, str(eval_root))
    
    print(f"项目根目录: {project_root}")
    print(f"评估根目录: {eval_root}")

async def test_evaluator_step_by_step():
    """逐步测试评估器"""
    print("\n=== 逐步测试评估器 ===")
    
    try:
        # 1. 导入评估器
        from core.evaluator import LegalSearchEvaluator
        print("✅ 评估器导入成功")
        
        # 2. 创建评估器实例
        evaluator = LegalSearchEvaluator()
        print("✅ 评估器创建成功")
        print(f"搜索引擎类型: {type(evaluator.search_engine).__name__}")
        
        # 3. 测试Ground Truth加载
        print("\n--- 测试Ground Truth加载 ---")
        gt_loaded = evaluator.ground_truth_loader.load()
        print(f"Ground Truth加载结果: {gt_loaded}")
        if gt_loaded:
            stats = evaluator.ground_truth_loader.get_statistics()
            print(f"数据统计: {stats}")
        
        # 4. 测试测试数据生成
        print("\n--- 测试测试数据生成 ---")
        test_data_loaded = evaluator.test_generator.load_data()
        print(f"测试数据加载结果: {test_data_loaded}")
        
        if test_data_loaded:
            test_queries = evaluator.test_generator.generate_all_test_queries()
            print(f"生成的测试查询类型: {list(test_queries.keys())}")
            for query_type, queries in test_queries.items():
                print(f"  {query_type}: {len(queries)} 个查询")
        
        # 5. 测试数据准备
        print("\n--- 测试数据准备 ---")
        prepare_result = await evaluator._prepare_data()
        print(f"数据准备结果: {prepare_result}")
        
        if prepare_result:
            print("✅ 数据准备成功，可以进行评估")
            
            # 6. 测试单个搜索
            print("\n--- 测试单个搜索 ---")
            if hasattr(evaluator, 'test_queries') and evaluator.test_queries:
                # 取第一个查询进行测试
                for query_type, queries in evaluator.test_queries.items():
                    if queries:
                        test_query = queries[0]
                        print(f"测试查询: {test_query}")
                        
                        search_result = await evaluator._execute_single_search(test_query)
                        print(f"搜索结果: {search_result}")
                        
                        # 测试评估
                        eval_result = evaluator._evaluate_single_result(test_query, search_result)
                        print(f"评估结果: {eval_result}")
                        break
        else:
            print("❌ 数据准备失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_simple_evaluation():
    """测试简单评估"""
    print("\n=== 测试简单评估 ===")
    
    try:
        from core.evaluator import LegalSearchEvaluator
        
        # 创建简单的测试查询
        simple_test_queries = {
            'crime_consistency': [
                {
                    'query_id': 'crime_1',
                    'query_type': 'crime_consistency',
                    'query_text': '盗窃罪',
                    'crime_name': '盗窃罪'
                }
            ]
        }
        
        evaluator = LegalSearchEvaluator()
        print("✅ 评估器创建成功")
        
        # 使用简单测试查询进行评估
        results = await evaluator.evaluate(test_queries=simple_test_queries)
        print("✅ 评估完成")
        print(f"评估结果摘要: {results.get('summary', {})}")
        
    except Exception as e:
        print(f"❌ 简单评估失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("开始测试评估流程...")
    print("=" * 50)
    
    # 设置路径
    setup_paths()
    
    # 逐步测试
    await test_evaluator_step_by_step()
    
    # 简单评估测试
    await test_simple_evaluation()
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    asyncio.run(main())
