#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法智导航项目初始化脚本 - 简化版
"""

import os
import sys
from pathlib import Path

def main():
    print("法智导航项目初始化检查")
    print("=" * 40)
    
    # 检查Python版本
    print(f"Python版本: {sys.version_info.major}.{sys.version_info.minor}")
    if sys.version_info < (3, 9):
        print("警告: Python版本过低，建议使用3.9+")
    
    # 创建必要目录
    dirs = ["data/processed", "data/embeddings", "data/indices", 
            "models/pretrained", "models/finetuned", "logs/app"]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("目录结构检查完成")
    
    # 检查数据文件
    data_files = ["data/raw/raw_laws(1).csv", "data/raw/raw_cases(1).csv"]
    for f in data_files:
        if Path(f).exists():
            size = Path(f).stat().st_size / 1024 / 1024
            print(f"数据文件: {f} ({size:.1f}MB)")
        else:
            print(f"缺失: {f}")
    
    # 检查配置文件
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("提示: 请复制.env.example为.env并配置")
        else:
            print("警告: 缺失环境配置文件")
    
    print("=" * 40)
    print("初始化检查完成")
    print("可以运行: python src/main.py")

if __name__ == "__main__":
    main()