
"""
测试新的数据加载管理器
"""

import sys
from pathlib import Path
import time

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_data_loader():
    """测试数据加载器"""
    print("=" * 60)
    print("测试数据加载管理器")
    print("=" * 60)
    
    try:
        from src.core.data_loader import get_data_loader, load_all_data
        
        # 获取数据加载器实例
        loader = get_data_loader()
        print(f"数据加载器创建成功")
        print(f"   项目根目录: {loader.project_root}")
        print(f"   向量目录: {loader.vectors_dir}")
        print(f"   原始数据目录: {loader.criminal_dir}")
        
        # 测试加载所有数据
        print("\n" + "=" * 40)
        print("加载所有数据...")
        start_time = time.time()
        stats = load_all_data()
        loading_time = time.time() - start_time
        
        print(f"数据加载完成，总耗时: {loading_time:.2f}秒")
        print(f"   总文档数: {stats['total_documents']}")
        print(f"   内存使用: {stats['memory_usage_mb']:.1f}MB")
        
        # 向量数据统计
        if 'vectors' in stats:
            vectors_stats = stats['vectors']
            print(f"\n数据统计 - 向量数据:")
            print(f"   法条向量: {vectors_stats.get('articles', 0)} 个")
            print(f"   案例向量: {vectors_stats.get('cases', 0)} 个")
            print(f"   加载时间: {vectors_stats.get('loading_time', 0):.2f}秒")
        
        # 模型统计
        if 'model' in stats:
            model_stats = stats['model']
            print(f"\n模型信息:")
            print(f"   状态: {model_stats.get('status')}")
            print(f"   模型: {model_stats.get('model_name')}")
            print(f"   加载时间: {model_stats.get('loading_time', 0):.2f}秒")
        
        # 测试内容获取
        print("\n" + "=" * 40)
        print("测试内容获取...")
        
        # 测试法条内容
        article_content = loader.get_article_content("article_1")
        if article_content:
            print(f"成功获取法条内容: {article_content[:100]}...")
        else:
            print("未能获取法条内容")
        
        # 测试案例内容
        case_content = loader.get_case_content("case_000001")
        if case_content:
            print(f"成功获取案例内容: {case_content[:100]}...")
        else:
            print("未能获取案例内容")
        
        # 测试查询编码
        print("\n" + "=" * 40)
        print("测试查询编码...")
        
        query_vector = loader.encode_query("盗窃他人财物")
        if query_vector is not None:
            print(f"成功编码查询，向量shape: {query_vector.shape}")
        else:
            print("查询编码失败")
        
        # 获取详细统计
        print("\n" + "=" * 40)
        print("系统统计信息:")
        detailed_stats = loader.get_stats()
        for key, value in detailed_stats.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_search_engine():
    """测试增强搜索引擎"""
    print("\n" + "=" * 60)
    print("测试增强搜索引擎")
    print("=" * 60)
    
    try:
        from src.engines.enhanced_search_engine import get_enhanced_search_engine
        
        # 获取搜索引擎
        engine = get_enhanced_search_engine()
        print("增强搜索引擎创建成功")
        
        # 加载数据
        load_stats = engine.load_data()
        print(f"数据加载状态: {load_stats['status']}")
        print(f"   总文档数: {load_stats['total_documents']}")
        
        # 测试基本搜索
        print("\n测试基本搜索...")
        results = engine.search("盗窃", top_k=3)
        print(f"搜索到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['type']} - {result.get('title', 'N/A')}")
            print(f"      相似度: {result['similarity']:.4f}")
            print(f"      预览: {result.get('content_preview', 'N/A')}")
        
        # 测试包含完整内容的搜索
        print("\n测试包含完整内容的搜索...")
        detailed_results = engine.search("盗窃", top_k=2, include_content=True)
        print(f"详细搜索到 {len(detailed_results)} 个结果:")
        for i, result in enumerate(detailed_results, 1):
            print(f"   {i}. {result['type']} - {result.get('title', 'N/A')}")
            if 'content' in result:
                content = result['content']
                print(f"      完整内容: {content[:150]}...")
            else:
                print("      无完整内容")
        
        # 测试分类搜索
        print("\n测试法条专项搜索...")
        articles_results = engine.search_articles_only("盗窃", top_k=2)
        print(f"法条搜索结果: {len(articles_results)} 个")
        
        print("\n测试案例专项搜索...")
        cases_results = engine.search_cases_only("盗窃", top_k=2)
        print(f"案例搜索结果: {len(cases_results)} 个")
        
        # 获取系统统计
        print("\n搜索引擎统计:")
        engine_stats = engine.get_stats()
        for key, value in engine_stats.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强搜索引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试新的数据管理系统")
    
    # 测试数据加载器
    loader_success = test_data_loader()
    
    # 测试增强搜索引擎
    engine_success = test_enhanced_search_engine()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"数据加载器: {'通过' if loader_success else '失败'}")
    print(f"增强搜索引擎: {'通过' if engine_success else '失败'}")
    
    if loader_success and engine_success:
        print("所有测试通过！新的数据管理系统工作正常")
        return 0
    else:
        print("部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit(main())