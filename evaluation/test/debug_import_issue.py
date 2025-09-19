#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彻底调试导入问题
"""

import sys
import os
from pathlib import Path

def debug_paths():
    """调试路径问题"""
    print("=== 路径调试 ===")
    
    current_file = Path(__file__).resolve()
    evaluation_root = current_file.parent.parent
    project_root = evaluation_root.parent
    
    print(f"当前文件: {current_file}")
    print(f"evaluation根目录: {evaluation_root}")
    print(f"项目根目录: {project_root}")
    
    # 检查关键目录
    src_dir = project_root / "src"
    print(f"src目录: {src_dir}")
    print(f"src目录存在: {src_dir.exists()}")
    
    if src_dir.exists():
        print(f"src目录内容: {list(src_dir.iterdir())}")
        
        init_file = src_dir / "__init__.py"
        print(f"src/__init__.py存在: {init_file.exists()}")
        
        if not init_file.exists():
            print("❌ 缺少src/__init__.py文件!")
            return False
    
    return True

def test_sys_path_setup():
    """测试sys.path设置"""
    print("\n=== sys.path设置测试 ===")
    
    current_file = Path(__file__).resolve()
    evaluation_root = current_file.parent.parent
    project_root = evaluation_root.parent
    
    print(f"添加前的sys.path长度: {len(sys.path)}")
    
    # 清理可能的重复路径
    for path in [str(project_root), str(evaluation_root)]:
        while path in sys.path:
            sys.path.remove(path)
    
    # 添加路径到最前面
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(evaluation_root))
    
    print(f"添加后的sys.path前5项:")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")
    
    return True

def test_direct_src_import():
    """直接测试src导入"""
    print("\n=== 直接测试src导入 ===")
    
    try:
        import src
        print(f"✅ src导入成功: {src}")
        print(f"src.__path__: {getattr(src, '__path__', 'None')}")
        
        try:
            import src.infrastructure
            print("✅ src.infrastructure导入成功")
            
            try:
                import src.infrastructure.search
                print("✅ src.infrastructure.search导入成功")
                
                try:
                    from src.infrastructure.search.vector_search_engine import get_enhanced_search_engine
                    print("✅ get_enhanced_search_engine导入成功")
                    return True
                except ImportError as e:
                    print(f"❌ get_enhanced_search_engine导入失败: {e}")
                    
            except ImportError as e:
                print(f"❌ src.infrastructure.search导入失败: {e}")
                
        except ImportError as e:
            print(f"❌ src.infrastructure导入失败: {e}")
            
    except ImportError as e:
        print(f"❌ src导入失败: {e}")
        
        # 手动检查Python能否找到src
        project_root = Path(__file__).resolve().parent.parent.parent
        src_path = project_root / "src"
        
        if src_path.exists() and str(project_root) in sys.path:
            print(f"src路径存在且项目根目录在sys.path中，但仍无法导入")
            print(f"可能原因: src目录缺少__init__.py文件")
            
    return False

def test_evaluator_import():
    """测试评估器导入"""
    print("\n=== 测试评估器导入 ===")
    
    try:
        from core.evaluator import LegalSearchEvaluator
        print("✅ 评估器导入成功")
        
        # 尝试创建实例
        evaluator = LegalSearchEvaluator()
        print("❌ 评估器创建应该失败（因为无法加载真实搜索引擎）")
        return False
        
    except RuntimeError as e:
        if "无法加载真实搜索引擎" in str(e):
            print("✅ 评估器正确拒绝使用模拟搜索引擎")
            return True
        else:
            print(f"❌ 意外的RuntimeError: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 评估器导入或创建失败: {e}")
        return False

def main():
    """主函数"""
    print("开始调试导入问题...")
    print("=" * 60)
    
    # 1. 调试路径
    paths_ok = debug_paths()
    
    # 2. 设置sys.path
    if paths_ok:
        test_sys_path_setup()
        
        # 3. 测试src导入
        src_import_ok = test_direct_src_import()
        
        # 4. 测试评估器
        evaluator_ok = test_evaluator_import()
        
        print("\n" + "=" * 60)
        print("调试结果:")
        print(f"路径检查: {'✅' if paths_ok else '❌'}")
        print(f"src导入: {'✅' if src_import_ok else '❌'}")
        print(f"评估器: {'✅' if evaluator_ok else '❌'}")
        
        if src_import_ok and evaluator_ok:
            print("\n🎉 导入问题已解决！")
        else:
            print("\n❌ 仍有问题需要解决")
            if not src_import_ok:
                print("建议: 检查src目录的__init__.py文件")

if __name__ == "__main__":
    main()
