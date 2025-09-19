#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的导入问题
"""

import sys
from pathlib import Path

def test_evaluator_with_real_search_engine():
    """测试使用真实搜索引擎的评估器"""
    print("=== 测试修复后的评估器 ===")
    
    # 设置路径
    eval_root = Path(__file__).resolve().parent.parent
    project_root = eval_root.parent
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(eval_root) not in sys.path:
        sys.path.insert(0, str(eval_root))
    
    try:
        from core.evaluator import LegalSearchEvaluator
        print("✅ 评估器导入成功")
        
        # 创建评估器
        evaluator = LegalSearchEvaluator()
        print("✅ 评估器创建成功")
        
        # 检查搜索引擎类型
        search_engine_type = type(evaluator.search_engine).__name__
        print(f"搜索引擎类型: {search_engine_type}")
        
        if search_engine_type == 'MockSearchEngine':
            print("❌ 仍在使用模拟搜索引擎")
            return False
        else:
            print("✅ 使用真实搜索引擎")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_import():
    """直接测试搜索引擎导入"""
    print("\n=== 直接测试搜索引擎导入 ===")
    
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        from src.infrastructure.search.vector_search_engine import get_enhanced_search_engine
        print("✅ 搜索引擎模块导入成功")
        
        search_engine = get_enhanced_search_engine()
        print(f"✅ 搜索引擎创建成功: {type(search_engine).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 搜索引擎导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("测试修复后的导入问题...")
    print("=" * 50)
    
    # 测试直接导入
    direct_import_ok = test_direct_import()
    
    # 测试评估器
    evaluator_ok = test_evaluator_with_real_search_engine()
    
    print("\n" + "=" * 50)
    if direct_import_ok and evaluator_ok:
        print("🎉 所有测试通过！评估系统可以使用真实搜索引擎")
    else:
        print("❌ 还有问题需要解决")

if __name__ == "__main__":
    main()
