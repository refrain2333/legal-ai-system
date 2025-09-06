#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能混合排序引擎 - 全面测试脚本
验证查询扩展和多信号融合排序的效果
"""

import sys
from pathlib import Path
import asyncio
import time
import json

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_intelligent_hybrid_ranking():
    """测试智能混合排序引擎的完整功能"""
    print("="*80)
    print("智能混合排序引擎 - 全面效果测试")
    print("="*80)
    
    try:
        from src.services.retrieval_service import get_retrieval_service
        service = await get_retrieval_service()
        
        print(f"服务版本: {service.stats.get('service_version', 'unknown')}")
        print(f"文档总数: {service.stats.get('total_documents', 0)}")
        hybrid_status = "启用" if service.hybrid_ranking_service else "禁用"
        print(f"混合排序: {hybrid_status}")
        
        # 测试用例 - 重点测试口语化查询
        test_cases = [
            {
                "query": "我打你",
                "description": "极端口语化 - 测试智能扩展",
                "expected": "故意伤害相关"
            },
            {
                "query": "他偷了我的钱",
                "description": "日常口语 - 财产犯罪",
                "expected": "盗窃罪相关"
            },
            {
                "query": "老板不给工资",
                "description": "劳动纠纷口语",
                "expected": "劳动法相关"
            },
            {
                "query": "撞车了怎么办",
                "description": "交通事故咨询",
                "expected": "交通法规"
            },
            {
                "query": "合同违约责任",
                "description": "标准法律术语 - 对照组",
                "expected": "合同法相关"
            },
            {
                "query": "想离婚分财产",
                "description": "婚姻家庭口语",
                "expected": "婚姻法相关"
            }
        ]
        
        comparison_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n【测试 {i}】: {query} ({description})")
            
            # 1. 原始语义检索（禁用智能排序）
            print("  原始语义检索:")
            start_time = time.time()
            result_original = await service.search(
                query, top_k=5, enable_intelligent_ranking=False
            )
            original_time = (time.time() - start_time) * 1000
            
            # 2. 智能混合排序检索
            print("  智能混合排序:")
            start_time = time.time()
            result_hybrid = await service.search(
                query, top_k=5, enable_intelligent_ranking=True
            )
            hybrid_time = (time.time() - start_time) * 1000
            
            # 3. 对比分析
            print(f"    响应时间: {original_time:.1f}ms → {hybrid_time:.1f}ms")
            
            # 显示查询扩展信息
            if 'results' in result_hybrid and result_hybrid['results']:
                first_result = result_hybrid['results'][0]
                if first_result.get('hybrid_enhanced'):
                    expansion_info = getattr(service.hybrid_ranking_service, '_last_expansion', None)
                    if hasattr(service.hybrid_ranking_service, 'expand_user_query'):
                        expansion_info = await service.hybrid_ranking_service.expand_user_query(query)
                        if expansion_info['expansion_applied']:
                            print(f"    查询扩展: {query} → {expansion_info['expanded_query']}")
                            for exp in expansion_info['expansions']:
                                print(f"      + {exp['term']} (置信度: {exp['confidence']:.3f})")
            
            # 对比前3个结果
            print("    结果对比:")
            for j in range(min(3, len(result_original.get('results', [])))):
                print(f"      结果 {j+1}:")
                
                # 原始结果
                if j < len(result_original['results']):
                    orig = result_original['results'][j]
                    title = orig.get('title', 'N/A')[:50]
                    score = orig.get('score', 0)
                    print(f"        原始: {score:.4f} - {title}...")
                
                # 混合排序结果
                if j < len(result_hybrid['results']):
                    hybrid = result_hybrid['results'][j]
                    title = hybrid.get('title', 'N/A')[:50]
                    final_score = hybrid.get('score', 0)
                    original_score = hybrid.get('original_score', final_score)
                    
                    print(f"        混合: {final_score:.4f} (原{original_score:.4f}) - {title}...")
                    
                    # 显示分数分解
                    if hybrid.get('score_breakdown'):
                        breakdown = hybrid['score_breakdown']
                        print(f"          分解: 语义{breakdown.get('semantic', 0):.3f} + "
                              f"扩展{breakdown.get('expansion', 0):.3f} + "
                              f"映射{breakdown.get('mapping', 0):.3f} + "
                              f"关键词{breakdown.get('keyword', 0):.3f}")
                    
                    # 显示映射关系
                    boost_details = hybrid.get('boost_details', {})
                    if boost_details.get('has_precise_mapping') or boost_details.get('has_fuzzy_mapping'):
                        mapping_type = "精确" if boost_details.get('has_precise_mapping') else "模糊"
                        print(f"          映射: {mapping_type}映射关系")
            
            # 收集对比数据
            original_avg_score = sum(r.get('score', 0) for r in result_original.get('results', [])[:3]) / min(3, len(result_original.get('results', [])))
            hybrid_avg_score = sum(r.get('score', 0) for r in result_hybrid.get('results', [])[:3]) / min(3, len(result_hybrid.get('results', [])))
            
            comparison_results.append({
                'query': query,
                'description': description,
                'original_avg_score': original_avg_score,
                'hybrid_avg_score': hybrid_avg_score,
                'improvement': hybrid_avg_score - original_avg_score,
                'improvement_percent': ((hybrid_avg_score - original_avg_score) / original_avg_score * 100) if original_avg_score > 0 else 0,
                'original_time': original_time,
                'hybrid_time': hybrid_time
            })
        
        # 4. 总体效果分析
        print(f"\n" + "="*80)
        print("总体效果分析")
        print("="*80)
        
        # 计算总体改进
        total_improvement = sum(r['improvement'] for r in comparison_results)
        avg_improvement = total_improvement / len(comparison_results)
        avg_improvement_percent = sum(r['improvement_percent'] for r in comparison_results) / len(comparison_results)
        
        avg_original_time = sum(r['original_time'] for r in comparison_results) / len(comparison_results)
        avg_hybrid_time = sum(r['hybrid_time'] for r in comparison_results) / len(comparison_results)
        
        print(f"测试查询数量: {len(comparison_results)}")
        print(f"平均相关度改进: {avg_improvement:.4f} ({avg_improvement_percent:+.1f}%)")
        print(f"平均响应时间: {avg_original_time:.1f}ms → {avg_hybrid_time:.1f}ms")
        
        # 按改进程度排序
        print(f"\n详细改进情况:")
        sorted_results = sorted(comparison_results, key=lambda x: x['improvement'], reverse=True)
        
        for result in sorted_results:
            improvement_str = f"{result['improvement']:+.4f} ({result['improvement_percent']:+.1f}%)"
            print(f"  {result['query'][:20]:20s} | {result['original_avg_score']:.4f} → {result['hybrid_avg_score']:.4f} | {improvement_str}")
        
        # 判断总体效果
        print(f"\n" + "="*50)
        if avg_improvement > 0.05:  # 5%以上改进
            print("智能混合排序效果显著，建议启用")
        elif avg_improvement > 0.02:  # 2%以上改进
            print("智能混合排序效果良好，建议启用")
        elif avg_improvement > 0:
            print("智能混合排序有轻微改进，可考虑启用")
        else:
            print("智能混合排序无明显改进，需要调优")
        
        print("="*50)
        
        return comparison_results
        
    except Exception as e:
        print(f"测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return []

async def test_query_expansion_only():
    """单独测试查询扩展功能"""
    print("\n" + "="*80)
    print("智能查询扩展 - 独立测试")
    print("="*80)
    
    try:
        from src.services.intelligent_hybrid_ranking import get_intelligent_hybrid_service
        hybrid_service = await get_intelligent_hybrid_service()
        
        test_queries = [
            "我打你",
            "他偷了我的钱", 
            "老板不给我工资",
            "撞车了",
            "想离婚",
            "合同违约"  # 对照：专业术语
        ]
        
        print("查询扩展效果测试:")
        
        for query in test_queries:
            expansion_result = await hybrid_service.expand_user_query(query, max_expansions=3)
            
            print(f"\n原查询: {query}")
            if expansion_result['expansion_applied']:
                print(f"扩展后: {expansion_result['expanded_query']}")
                print(f"扩展项:")
                for i, exp in enumerate(expansion_result['expansions'], 1):
                    print(f"  {i}. {exp['term']} (相似度: {exp['similarity']:.3f}, 置信度: {exp['confidence']:.3f})")
                    print(f"     源表达: {exp['source_colloquial']}")
            else:
                print("无扩展 (未找到相似表达)")
        
        # 显示扩展索引统计
        stats = hybrid_service.get_service_stats()
        print(f"\n扩展索引统计:")
        print(f"  扩展对数量: {stats['expansion_pairs_count']}")
        print(f"  精确映射: {stats['precise_mappings_count']}")
        print(f"  模糊映射: {stats['fuzzy_mappings_count']}")
        
    except Exception as e:
        print(f"查询扩展测试出错: {e}")

async def main():
    """主测试函数"""
    try:
        # 1. 完整功能测试
        results = await test_intelligent_hybrid_ranking()
        
        # 2. 查询扩展单独测试
        await test_query_expansion_only()
        
        # 3. 保存测试结果
        if results:
            with open('intelligent_hybrid_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n测试结果已保存到: intelligent_hybrid_test_results.json")
        
    except Exception as e:
        print(f"测试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())