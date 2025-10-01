#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目结构验证工具 - 标准化后版本
检验项目是否符合标准结构规范
"""

import os
from pathlib import Path

def verify_project_structure():
    """验证项目结构是否符合标准"""
    
    print("="*60)
    print("项目结构标准化验证")
    print("="*60)
    
    # 标准目录结构定义
    required_structure = {
        'src/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'main.py']
        },
        'src/api/': {
            'type': 'directory', 
            'required': True,
            'files': ['__init__.py', 'app.py', 'search_routes.py']
        },
        'src/models/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'semantic_embedding.py']
        },
        'src/services/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'retrieval_service.py']
        },
        'src/data/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'full_dataset_processor.py']
        },
        'src/config/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'settings.py']
        },
        'src/utils/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'logger.py']
        },
        'tests/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py', 'conftest.py', 'test_core_functionality.py']
        },
        'tools/': {
            'type': 'directory',
            'required': True,
            'files': ['__init__.py']
        },
        'data/': {
            'type': 'directory',
            'required': True,
            'subdirs': ['raw', 'processed', 'indices']
        },
        'docs/': {
            'type': 'directory',
            'required': True,
            'subdirs': ['tasks']
        }
    }
    
    # 检查根目录不应有散乱的Python文件
    prohibited_root_files = [
        'final_performance_test.py',
        'run_server.py', 
        'verify_system_structure.py',
        'test_*.py'
    ]
    
    # 验证结果
    results = {
        'structure_correct': True,
        'issues': [],
        'suggestions': []
    }
    
    # 1. 检查目录结构
    print("1. 检查目录结构...")
    for path, config in required_structure.items():
        full_path = Path(path)
        
        if config['required'] and not full_path.exists():
            results['structure_correct'] = False
            results['issues'].append(f"缺少必需目录: {path}")
            print(f"   ERROR {path}")
        else:
            print(f"   OK {path}")
            
            # 检查必需文件
            if 'files' in config:
                for file in config['files']:
                    file_path = full_path / file
                    if not file_path.exists():
                        results['issues'].append(f"缺少必需文件: {path}/{file}")
                        print(f"     MISSING {file}")
                    else:
                        print(f"     OK {file}")
            
            # 检查子目录
            if 'subdirs' in config:
                for subdir in config['subdirs']:
                    subdir_path = full_path / subdir
                    if not subdir_path.exists():
                        results['issues'].append(f"缺少子目录: {path}/{subdir}")
                        print(f"     MISSING {subdir}/")
                    else:
                        print(f"     OK {subdir}/")
    
    # 2. 检查根目录的禁止文件
    print("\\n2. 检查根目录清洁度...")
    root_python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    allowed_root_files = ['app.py']  # 标准启动脚本
    
    for file in root_python_files:
        if file not in allowed_root_files:
            results['structure_correct'] = False
            results['issues'].append(f"根目录发现不应存在的Python文件: {file}")
            print(f"   ❌ {file} (应移动到合适目录)")
        else:
            print(f"   ✅ {file}")
    
    # 3. 检查重复目录
    print("\\n3. 检查重复目录...")
    if Path('src/tests').exists():
        results['structure_correct'] = False
        results['issues'].append("发现重复的测试目录: src/tests/ (应只使用 tests/)")
        print("   ❌ src/tests/ 存在")
    else:
        print("   ✅ 无重复测试目录")
    
    # 4. 检查文件数量 (避免冗余)
    print("\\n4. 检查模块冗余性...")
    models_files = list(Path('src/models').glob('*.py'))
    models_count = len([f for f in models_files if f.name != '__init__.py'])
    
    if models_count <= 2:
        print(f"   ✅ models模块数量合理 ({models_count}个)")
    else:
        results['suggestions'].append(f"models目录文件较多({models_count}个)，建议检查是否有重复功能")
        print(f"   ⚠️ models模块较多 ({models_count}个)")
    
    # 输出验证结果
    print("\\n" + "="*60)
    print("验证结果:")
    print("="*60)
    
    if results['structure_correct']:
        print("✅ 项目结构标准化验证通过")
    else:
        print("❌ 项目结构存在问题")
        
    if results['issues']:
        print("\\n📋 需要修复的问题:")
        for issue in results['issues']:
            print(f"  - {issue}")
    
    if results['suggestions']:
        print("\\n💡 优化建议:")
        for suggestion in results['suggestions']:
            print(f"  - {suggestion}")
    
    if results['structure_correct'] and not results['suggestions']:
        print("\\n🎉 项目结构完全符合标准规范!")
    
    return results['structure_correct']

if __name__ == "__main__":
    success = verify_project_structure()
    if not success:
        exit(1)