#!/usr/bin/env python3
"""
数据文件验证脚本
检查CSV文件格式、编码、基本统计信息
"""

import pandas as pd
import sys
from pathlib import Path

def validate_csv_file(file_path: str, expected_columns: list = None):
    """验证CSV文件"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        # 尝试读取CSV
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"✅ {path.name}")
        print(f"   - 行数: {len(df):,}")
        print(f"   - 列数: {len(df.columns)}")
        print(f"   - 文件大小: {path.stat().st_size / 1024 / 1024:.1f}MB")
        
        if expected_columns:
            missing_cols = set(expected_columns) - set(df.columns)
            if missing_cols:
                print(f"   ⚠️ 缺失列: {missing_cols}")
            else:
                print(f"   ✅ 列检查通过")
        
        # 显示列名
        print(f"   - 列名: {list(df.columns)}")
        
        # 检查空值
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"   ⚠️ 空值情况: {null_counts[null_counts > 0].to_dict()}")
        else:
            print(f"   ✅ 无空值")
        
        return True
        
    except UnicodeDecodeError:
        try:
            # 尝试GBK编码
            df = pd.read_csv(file_path, encoding='gbk')
            print(f"✅ {path.name} (GBK编码)")
            print(f"   - 行数: {len(df):,}")
            print(f"   - 列数: {len(df.columns)}")
            return True
        except Exception as e:
            print(f"❌ 编码问题: {file_path} - {e}")
            return False
    except Exception as e:
        print(f"❌ 读取失败: {file_path} - {e}")
        return False

def main():
    """主函数"""
    print("📊 法智导航数据文件验证")
    print("=" * 50)
    
    # 验证数据文件
    data_files = [
        ("data/raw/raw_laws(1).csv", ["id", "title", "content"]),  # 期望的列名
        ("data/raw/raw_cases(1).csv", None),
        ("data/raw/精确映射表.csv", None),
        ("data/raw/精确+模糊匹配映射表.csv", None)
    ]
    
    all_valid = True
    for file_path, expected_cols in data_files:
        print(f"\n📄 验证文件: {file_path}")
        if not validate_csv_file(file_path, expected_cols):
            all_valid = False
    
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 所有数据文件验证通过！")
    else:
        print("⚠️ 部分数据文件存在问题，请检查")
        sys.exit(1)

if __name__ == "__main__":
    main()