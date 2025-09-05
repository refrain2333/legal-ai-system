#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤1: 环境检查
检查Python版本、虚拟环境状态、依赖包安装情况
"""

import os
import sys
import subprocess

def check_python_version():
    """检查Python版本是否满足要求"""
    required = (3, 9)
    current = sys.version_info[:2]
    
    print(f"Python版本: {current[0]}.{current[1]}")
    if current >= required:
        print("✅ Python版本符合要求")
        return True
    else:
        print(f"❌ 需要Python {required[0]}.{required[1]}+")
        return False

def check_virtual_env():
    """检查虚拟环境状态"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if conda_env:
        print(f"✅ Conda环境: {conda_env}")
        return True, 'conda', conda_env
    elif venv_active:
        print("✅ Python虚拟环境已激活")
        return True, 'venv', 'virtual-env'
    else:
        print("⚠️  当前在全局环境 - 强烈建议使用虚拟环境")
        return False, 'global', 'global'

def check_conda_available():
    """检查conda是否可用"""
    try:
        subprocess.run(['conda', '--version'], capture_output=True, check=True)
        return True
    except:
        return False

def check_dependencies():
    """检查关键依赖包"""
    critical = ['torch', 'transformers', 'fastapi', 'pydantic']
    missing = []
    
    for pkg in critical:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    return missing

def print_recommendations(in_venv, env_type, missing_deps):
    """打印建议步骤"""
    print("\n🎯 建议步骤:")
    
    step = 1
    if not in_venv:
        print(f"{step}. 创建虚拟环境:")
        if check_conda_available():
            print("   conda create -n legal-ai python=3.9 -y")
            print("   conda activate legal-ai")
        else:
            print("   python -m venv venv")
            print("   venv\\Scripts\\activate  # Windows")
        step += 1
    
    if missing_deps:
        print(f"{step}. 安装依赖:")
        print("   pip install -r requirements_fixed.txt")
        step += 1
    
    print(f"{step}. 运行项目初始化:")
    print("   python scripts/init/step2_project_setup.py")

def main():
    print("="*50)
    print("步骤1: 环境检查")
    print("="*50)
    
    # 检查各项
    python_ok = check_python_version()
    in_venv, env_type, env_name = check_virtual_env()
    missing_deps = check_dependencies()
    
    print("\n📋 检查结果:")
    print(f"Python: {'✅' if python_ok else '❌'}")
    print(f"虚拟环境: {'✅' if in_venv else '⚠️'}")
    print(f"依赖包: {'✅' if not missing_deps else f'❌ 缺失{len(missing_deps)}个'}")
    
    if missing_deps:
        print(f"缺失: {', '.join(missing_deps)}")
    
    # 打印建议
    print_recommendations(in_venv, env_type, missing_deps)
    
    print("\n" + "="*50)
    
    if python_ok and in_venv and not missing_deps:
        print("✅ 环境检查通过，可以继续下一步!")
        return 0
    else:
        print("⚠️  请按建议解决问题后重新运行")
        return 1

if __name__ == "__main__":
    sys.exit(main())