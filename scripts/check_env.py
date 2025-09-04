#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法智导航项目 - 自动环境检查和设置脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_conda():
    """检查是否有conda"""
    try:
        result = subprocess.run(['conda', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_virtual_env():
    """检查是否在虚拟环境中"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def get_current_env_name():
    """获取当前环境名称"""
    if 'CONDA_DEFAULT_ENV' in os.environ:
        return os.environ['CONDA_DEFAULT_ENV']
    elif check_virtual_env():
        return "虚拟环境"
    else:
        return "全局环境"

def check_required_packages():
    """检查必需的包是否安装"""
    required_packages = ['torch', 'transformers', 'fastapi', 'pydantic']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def main():
    print("法智导航 - 环境状态检查")
    print("=" * 40)
    
    # 检查Python版本
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"Python版本: {python_version}")
    
    # 检查Python路径
    print(f"Python路径: {sys.executable}")
    
    # 检查当前环境
    env_name = get_current_env_name()
    print(f"当前环境: {env_name}")
    
    # 检查是否在虚拟环境
    in_venv = check_virtual_env()
    print(f"虚拟环境: {'是' if in_venv else '否'}")
    
    # 检查conda
    has_conda = check_conda()
    print(f"Conda可用: {'是' if has_conda else '否'}")
    
    print("-" * 40)
    
    # 检查依赖包
    missing = check_required_packages()
    if missing:
        print(f"缺失的关键包: {', '.join(missing)}")
        print("\n建议操作:")
        
        if not in_venv:
            print("⚠️  您当前在全局环境中，强烈建议使用虚拟环境！")
            print("\n推荐步骤:")
            if has_conda:
                print("1. conda create -n legal-ai python=3.9 -y")
                print("2. conda activate legal-ai") 
            else:
                print("1. python -m venv venv")
                print("2. venv\\Scripts\\activate  # Windows")
            print("3. pip install -r requirements.txt")
        else:
            print("可以安装依赖:")
            print("pip install -r requirements.txt")
    else:
        print("✓ 所有关键包已安装")
        if in_venv:
            print("✓ 环境配置良好，可以开始开发")
        else:
            print("⚠️  建议使用虚拟环境以避免依赖冲突")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()