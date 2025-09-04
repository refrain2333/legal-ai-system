#!/usr/bin/env python3
"""
法智导航项目初始化脚本
检查环境、创建必要目录、验证数据文件等
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 9):
        print("Python版本过低，需要Python 3.9+")
        return False
    print(f"Python版本: {sys.version}")
    return True

def check_directories():
    """检查并创建必要的目录"""
    required_dirs = [
        "data/processed",
        "data/embeddings", 
        "data/indices",
        "models/pretrained",
        "models/finetuned",
        "models/checkpoints",
        "logs/app",
        "logs/access",
        "logs/error"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {dir_path}")
        else:
            print(f"✅ 目录已存在: {dir_path}")
    
    return True

def check_data_files():
    """检查数据文件是否存在"""
    data_files = [
        "data/raw/raw_laws(1).csv",
        "data/raw/raw_cases(1).csv", 
        "data/raw/精确映射表.csv",
        "data/raw/精确+模糊匹配映射表.csv"
    ]
    
    all_exist = True
    for file_path in data_files:
        path = Path(file_path)
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"✅ 数据文件: {file_path} ({size_mb:.1f}MB)")
        else:
            print(f"❌ 缺失数据文件: {file_path}")
            all_exist = False
    
    return all_exist

def check_config_file():
    """检查环境配置文件"""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("⚠️ 未找到.env文件，请复制.env.example为.env并配置")
            return False
        else:
            print("❌ 缺失环境配置文件模板")
            return False
    else:
        print("✅ 环境配置文件存在")
        return True

def check_dependencies():
    """检查关键依赖是否安装"""
    try:
        import torch
        import transformers
        import fastapi
        import pydantic
        print("✅ 关键依赖包已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺失依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("法智导航项目初始化检查")
    print("=" * 50)
    
    checks = [
        ("Python版本检查", check_python_version),
        ("目录结构检查", check_directories),
        ("数据文件检查", check_data_files),
        ("配置文件检查", check_config_file),
        ("依赖包检查", check_dependencies)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("项目初始化检查完成，所有条件满足！")
        print("可以运行: python src/main.py")
    else:
        print("存在问题需要解决，请按照上述提示处理")
        sys.exit(1)

if __name__ == "__main__":
    main()