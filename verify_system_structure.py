#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的系统结构
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有关键模块的导入"""
    print("测试模块导入...")
    
    try:
        # 测试models模块
        print("1. 测试models模块...")
        from src.models.semantic_embedding import SemanticTextEmbedding
        print("   ✅ semantic_embedding 导入成功")
        
        # 测试data模块  
        print("2. 测试data模块...")
        from src.data.full_dataset_processor import FullDatasetProcessor
        print("   ✅ full_dataset_processor 导入成功")
        
        # 测试services模块
        print("3. 测试services模块...")
        from src.services.retrieval_service import get_retrieval_service
        print("   ✅ retrieval_service 导入成功")
        
        print("\\n🎉 所有关键模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"\\n❌ 导入失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    print("\\n检查目录结构...")
    
    expected_dirs = [
        'src/models',
        'src/services', 
        'src/data',
        'src/tests',
        'src/utils',
        'src/api',
        'src/config',
        'data/indices',
        'data/processed'
    ]
    
    all_exist = True
    for dir_path in expected_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} (缺失)")
            all_exist = False
    
    return all_exist

def test_key_files():
    """测试关键文件是否存在"""
    print("\\n检查关键文件...")
    
    key_files = [
        'src/models/semantic_embedding.py',
        'src/data/full_dataset_processor.py',
        'src/services/retrieval_service.py',
        'data/indices/complete_semantic_index.pkl',
        'data/processed/full_dataset.pkl'
    ]
    
    all_exist = True
    for file_path in key_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if file_path.endswith('.pkl'):
                size_mb = size / (1024 * 1024)
                print(f"   ✅ {file_path} ({size_mb:.1f}MB)")
            else:
                print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (缺失)")
            all_exist = False
    
    return all_exist

async def test_service_functionality():
    """测试服务功能"""
    print("\\n测试服务功能...")
    
    try:
        from src.services.retrieval_service import get_retrieval_service
        
        print("   初始化检索服务...")
        service = await get_retrieval_service()
        
        print("   执行测试查询...")
        result = await service.search("合同违约责任", top_k=3)
        
        if result['total'] > 0:
            print(f"   ✅ 查询成功: {result['total']} 个结果")
            print(f"   ✅ 最高分数: {result['results'][0]['score']:.4f}")
            return True
        else:
            print("   ❌ 查询无结果")
            return False
            
    except Exception as e:
        print(f"   ❌ 服务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*50)
    print("法智导航 - 系统结构修复验证")
    print("="*50)
    
    # 1. 测试目录结构
    dir_ok = test_directory_structure()
    
    # 2. 测试文件存在
    files_ok = test_key_files()
    
    # 3. 测试导入
    imports_ok = test_imports()
    
    # 4. 测试服务功能
    if imports_ok:
        import asyncio
        service_ok = asyncio.run(test_service_functionality())
    else:
        service_ok = False
    
    # 总结
    print("\\n" + "="*50)
    print("修复验证结果:")
    print("="*50)
    print(f"目录结构: {'✅ 正常' if dir_ok else '❌ 有问题'}")
    print(f"关键文件: {'✅ 存在' if files_ok else '❌ 缺失'}")
    print(f"模块导入: {'✅ 成功' if imports_ok else '❌ 失败'}")
    print(f"服务功能: {'✅ 正常' if service_ok else '❌ 异常'}")
    
    all_ok = all([dir_ok, files_ok, imports_ok, service_ok])
    
    if all_ok:
        print("\\n🎉 系统结构修复成功！所有测试通过")
    else:
        print("\\n⚠️ 系统还存在问题，需要进一步修复")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n建议检查上述错误信息并修复")
        sys.exit(1)