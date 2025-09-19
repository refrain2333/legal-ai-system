#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据生成问题
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

async def test_data_preparation():
    """测试数据准备过程"""
    print("=== 测试数据准备过程 ===")
    
    try:
        from core.evaluator import LegalSearchEvaluator
        evaluator = LegalSearchEvaluator()
        
        print(f"✅ 评估器创建成功")
        print(f"搜索引擎类型: {type(evaluator.search_engine).__name__}")
        print(f"测试生成器类型: {type(evaluator.test_generator).__name__}")
        
        # 测试Ground Truth加载
        print("\n--- 测试Ground Truth加载 ---")
        gt_result = evaluator.ground_truth_loader.load()
        print(f"Ground Truth加载结果: {gt_result}")
        
        # 测试测试数据加载
        print("\n--- 测试测试数据加载 ---")
        try:
            test_data_result = evaluator.test_generator.load_data()
            print(f"测试数据加载结果: {test_data_result}")
            
            if test_data_result:
                test_queries = evaluator.test_generator.generate_all_test_queries()
                print(f"生成的测试查询: {len(test_queries)} 种类型")
                for query_type, queries in test_queries.items():
                    print(f"  {query_type}: {len(queries)} 个查询")
        except Exception as e:
            print(f"❌ 测试数据加载失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试数据准备
        print("\n--- 测试完整数据准备 ---")
        try:
            prepare_result = await evaluator._prepare_data()
            print(f"数据准备结果: {prepare_result}")
            
            if prepare_result:
                print("✅ 数据准备成功！")
                # 简单评估测试
                simple_queries = {
                    'crime_consistency': [
                        {
                            'query_id': 'crime_1',
                            'query_type': 'crime_consistency',
                            'query_text': '盗窃罪',
                            'crime_name': '盗窃罪'
                        }
                    ]
                }
                
                print("\n--- 测试简单评估 ---")
                result = await evaluator.evaluate(test_queries=simple_queries)
                print("✅ 评估完成！")
                print(f"评估摘要: {result.get('summary', {})}")
            else:
                print("❌ 数据准备失败")
                
        except Exception as e:
            print(f"❌ 数据准备异常: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    setup_paths()
    asyncio.run(test_data_preparation())

if __name__ == "__main__":
    main()
