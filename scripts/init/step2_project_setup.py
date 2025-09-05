#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤2: 项目设置
创建必要目录、配置环境文件、验证数据
"""

import os
import sys
from pathlib import Path
import shutil

def create_directories():
    """创建项目必需目录"""
    dirs = [
        "data/processed", "data/embeddings", "data/indices", "data/cache",
        "models/pretrained", "models/finetuned", "models/checkpoints", 
        "logs/app", "logs/error", "temp/processing"
    ]
    
    created = 0
    for d in dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created += 1
    
    print(f"✅ 目录结构: {created}个新目录已创建")
    return True

def setup_config():
    """设置配置文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy2(env_example, env_file)
            print("✅ 环境配置: .env文件已创建")
            return True
        else:
            print("❌ 缺失.env.example模板")
            return False
    else:
        print("✅ 环境配置: .env文件已存在")
        return True

def check_data_files():
    """检查数据文件"""
    files = [
        "data/raw/raw_laws(1).csv",
        "data/raw/raw_cases(1).csv", 
        "data/raw/精确映射表.csv",
        "data/raw/精确+模糊匹配映射表.csv"
    ]
    
    existing = []
    missing = []
    total_size = 0
    
    for f in files:
        path = Path(f)
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            existing.append((f, size_mb))
            total_size += size_mb
        else:
            missing.append(f)
    
    if existing:
        print(f"✅ 数据文件: {len(existing)}个文件 (总计{total_size:.1f}MB)")
    
    if missing:
        print(f"❌ 缺失文件: {len(missing)}个")
        for f in missing:
            print(f"   {f}")
        return False
    
    return True

def verify_dependencies():
    """最终依赖验证"""
    required = [
        'torch', 'transformers', 'sentence_transformers', 'faiss-cpu',
        'fastapi', 'uvicorn', 'pydantic', 'loguru'
    ]
    
    installed = 0
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            installed += 1
        except ImportError:
            pass
    
    print(f"✅ 依赖包: {installed}/{len(required)}个已安装")
    return installed == len(required)

def main():
    print("="*50)
    print("步骤2: 项目设置")
    print("="*50)
    
    # 执行设置步骤
    print("\n📋 创建目录结构...")
    dirs_ok = create_directories()
    
    print("\n📋 设置配置文件...")
    config_ok = setup_config()
    
    print("\n📋 检查数据文件...")
    data_ok = check_data_files()
    
    print("\n📋 验证依赖...")
    deps_ok = verify_dependencies()
    
    # 总结
    print("\n📊 设置结果:")
    print(f"目录结构: {'✅' if dirs_ok else '❌'}")
    print(f"配置文件: {'✅' if config_ok else '❌'}")
    print(f"数据文件: {'✅' if data_ok else '❌'}")
    print(f"依赖包: {'✅' if deps_ok else '❌'}")
    
    all_ok = dirs_ok and config_ok and data_ok and deps_ok
    
    print("\n🎯 下一步:")
    if all_ok:
        print("✅ 项目设置完成!")
        print("运行: python scripts/init/step3_final_check.py")
    else:
        if not data_ok:
            print("1. 请将数据文件放入 data/raw/ 目录")
        if not deps_ok:
            print("2. 安装缺失依赖: pip install -r requirements_fixed.txt")
        print("3. 重新运行此脚本")
    
    print("="*50)
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())