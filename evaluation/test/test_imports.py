#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入问题的诊断脚本
"""

import sys
from pathlib import Path

def test_project_structure():
    """测试项目结构"""
    print("=== 项目结构检测 ===")
    
    # 设置路径
    project_root = Path(__file__).resolve().parent.parent.parent
    print(f"项目根目录: {project_root}")
    
    # 检查关键目录和文件
    checks = [
        ("src目录", project_root / "src"),
        ("src/__init__.py", project_root / "src" / "__init__.py"),
        ("src/infrastructure", project_root / "src" / "infrastructure"),
        ("src/infrastructure/__init__.py", project_root / "src" / "infrastructure" / "__init__.py"),
        ("src/infrastructure/search", project_root / "src" / "infrastructure" / "search"),
        ("src/infrastructure/search/__init__.py", project_root / "src" / "infrastructure" / "search" / "__init__.py"),
        ("vector_search_engine.py", project_root / "src" / "infrastructure" / "search" / "vector_search_engine.py"),
        ("src/config", project_root / "src" / "config"),
        ("src/config/settings.py", project_root / "src" / "config" / "settings.py"),
    ]
    
    for name, path in checks:
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")
    
    return project_root

def test_sys_path_setup(project_root):
    """测试sys.path设置"""
    print("\n=== sys.path设置测试 ===")
    
    # 添加项目根目录到sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ 已添加到sys.path: {project_root}")
    else:
        print(f"✅ 已在sys.path中: {project_root}")
    
    print(f"当前sys.path前5项:")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")

def test_module_imports(project_root):
    """测试模块导入"""
    print("\n=== 模块导入测试 ===")
    
    # 测试各级模块导入
    import_tests = [
        ("src", "import src"),
        ("src.infrastructure", "import src.infrastructure"),
        ("src.infrastructure.search", "import src.infrastructure.search"),
        ("src.config", "import src.config"),
        ("src.config.settings", "import src.config.settings"),
        ("vector_search_engine", "from src.infrastructure.search.vector_search_engine import get_enhanced_search_engine"),
    ]
    
    for name, import_stmt in import_tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}: 导入成功")
        except Exception as e:
            print(f"❌ {name}: 导入失败 - {e}")

def test_search_engine_creation():
    """测试搜索引擎创建"""
    print("\n=== 搜索引擎创建测试 ===")
    
    try:
        from src.infrastructure.search.vector_search_engine import get_enhanced_search_engine
        print("✅ 搜索引擎模块导入成功")
        
        # 尝试创建搜索引擎实例
        search_engine = get_enhanced_search_engine()
        print(f"✅ 搜索引擎实例创建成功: {type(search_engine).__name__}")
        
        # 测试数据加载
        print("开始测试数据加载...")
        load_result = search_engine.load_data()
        print(f"数据加载结果: {load_result}")
        
        if load_result.get('status') in ['success', 'already_loaded']:
            print("✅ 搜索引擎数据加载成功")
            return search_engine
        else:
            print(f"❌ 搜索引擎数据加载失败: {load_result}")
            return None
            
    except Exception as e:
        print(f"❌ 搜索引擎创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_evaluator_creation():
    """测试评估器创建"""
    print("\n=== 评估器创建测试 ===")
    
    try:
        # 添加评估系统路径
        eval_root = Path(__file__).resolve().parent.parent
        if str(eval_root) not in sys.path:
            sys.path.insert(0, str(eval_root))
        
        from core.evaluator import LegalSearchEvaluator
        print("✅ 评估器模块导入成功")
        
        # 创建评估器实例
        evaluator = LegalSearchEvaluator()
        print("✅ 评估器实例创建成功")
        
        # 检查组件状态
        print(f"搜索引擎类型: {type(evaluator.search_engine).__name__}")
        print(f"测试生成器类型: {type(evaluator.test_generator).__name__}")
        print(f"Ground Truth加载状态: {evaluator.ground_truth_loader.loaded}")
        
        return evaluator
        
    except Exception as e:
        print(f"❌ 评估器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主测试函数"""
    print("开始诊断评估系统导入问题...")
    print("=" * 50)
    
    # 1. 检查项目结构
    project_root = test_project_structure()
    
    # 2. 设置sys.path
    test_sys_path_setup(project_root)
    
    # 3. 测试模块导入
    test_module_imports(project_root)
    
    # 4. 测试搜索引擎创建
    search_engine = test_search_engine_creation()
    
    # 5. 测试评估器创建
    evaluator = test_evaluator_creation()
    
    print("\n" + "=" * 50)
    if search_engine and evaluator and type(evaluator.search_engine).__name__ != 'MockSearchEngine':
        print("🎉 所有测试通过！评估系统可以使用真实搜索引擎")
    elif evaluator:
        print("⚠️  评估器创建成功，但使用的是模拟搜索引擎")
    else:
        print("❌ 评估系统存在问题，需要进一步修复")

if __name__ == "__main__":
    main()
