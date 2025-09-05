#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤3: 最终检查
全面验证项目是否ready，可以开始开发
"""

import sys
import os
from pathlib import Path

def final_env_check():
    """最终环境检查"""
    print("🔍 环境状态...")
    
    # Python版本
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python_ok = sys.version_info >= (3, 9)
    print(f"   Python {py_version}: {'✅' if python_ok else '❌'}")
    
    # 虚拟环境
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    env_ok = conda_env or venv_active
    
    if conda_env:
        print(f"   Conda环境 ({conda_env}): ✅")
    elif venv_active:
        print(f"   Python虚拟环境: ✅")
    else:
        print(f"   虚拟环境: ❌ 未使用")
    
    return python_ok and env_ok

def final_structure_check():
    """最终结构检查"""
    print("🔍 项目结构...")
    
    required_dirs = [
        "src/api", "src/config", "data/raw", "logs/app", 
        "models/pretrained", "data/processed"
    ]
    
    missing_dirs = []
    for d in required_dirs:
        if not Path(d).exists():
            missing_dirs.append(d)
    
    if missing_dirs:
        print(f"   目录结构: ❌ 缺失{len(missing_dirs)}个")
        return False
    else:
        print(f"   目录结构: ✅")
        return True

def final_data_check():
    """最终数据检查"""
    print("🔍 数据文件...")
    
    data_files = [
        "data/raw/raw_laws(1).csv",
        "data/raw/raw_cases(1).csv"
    ]
    
    total_size = 0
    missing = 0
    
    for f in data_files:
        path = Path(f)
        if path.exists():
            total_size += path.stat().st_size / 1024 / 1024
        else:
            missing += 1
    
    if missing == 0:
        print(f"   数据文件: ✅ (总计{total_size:.1f}MB)")
        return True
    else:
        print(f"   数据文件: ❌ 缺失{missing}个")
        return False

def final_config_check():
    """最终配置检查"""
    print("🔍 配置文件...")
    
    config_files = [".env", "requirements_fixed.txt"]
    missing = []
    
    for f in config_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        print(f"   配置文件: ❌ 缺失{len(missing)}个")
        return False
    else:
        print(f"   配置文件: ✅")
        return True

def final_deps_check():
    """最终依赖检查"""
    print("🔍 核心依赖...")
    
    core_deps = ['torch', 'transformers', 'fastapi', 'pydantic', 'loguru']
    installed = 0
    
    for dep in core_deps:
        try:
            __import__(dep)
            installed += 1
        except ImportError:
            pass
    
    if installed == len(core_deps):
        print(f"   核心依赖: ✅ ({installed}/{len(core_deps)})")
        return True
    else:
        print(f"   核心依赖: ❌ ({installed}/{len(core_deps)})")
        return False

def print_startup_guide():
    """打印启动指南"""
    print("\n🚀 项目启动指南:")
    print("   1. 启动开发服务器:")
    print("      python src/main.py")
    print("")
    print("   2. 访问API文档:")
    print("      http://localhost:5005/docs")
    print("")
    print("   3. 常用开发命令:")
    print("      pytest                    # 运行测试")
    print("      black src/ tests/        # 代码格式化") 
    print("      python scripts/validate_data.py  # 数据验证")

def print_troubleshooting():
    """打印问题解决指南"""
    print("\n🔧 问题解决:")
    print("   环境问题: python scripts/init/step1_env_check.py")
    print("   配置问题: python scripts/init/step2_project_setup.py")
    print("   数据问题: 确保data/raw/目录有完整数据文件")

def main():
    print("="*50)
    print("步骤3: 最终检查")
    print("="*50)
    
    # 执行各项检查
    checks = [
        final_env_check(),
        final_structure_check(), 
        final_data_check(),
        final_config_check(),
        final_deps_check()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 恭喜! 项目已完全ready!")
        print_startup_guide()
        return_code = 0
    else:
        print("⚠️  还有问题需要解决")
        print_troubleshooting()
        return_code = 1
    
    print("="*50)
    return return_code

if __name__ == "__main__":
    sys.exit(main())