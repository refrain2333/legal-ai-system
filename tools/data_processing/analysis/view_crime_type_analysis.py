#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看 crime_type_analysis.pkl 内容的辅助脚本

用法::
    python view_crime_type_analysis.py [pkl_path] [--crime "盗窃罪"] [--top K]

功能:
    1. 读取罪名分析字典 (crime_type -> stats)。
    2. 若指定 --crime, 输出该罪名的详细统计。
    3. 否则按案例数降序输出前 K 个罪名。
"""

import sys
import pickle
from pathlib import Path
from argparse import ArgumentParser
from typing import Dict, Any


def load_analysis(pkl_path: Path) -> Dict[str, Any]:
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    if not isinstance(data, dict):
        raise ValueError("数据格式异常，预期为 dict[str, dict]")
    return data


def show_crime_detail(crime: str, stats: Dict[str, Any]):
    print(f"罪名: {crime}")
    print(f"案例总数: {stats['case_count']}")
    print(f"涉及条文: {', '.join(map(str, stats['related_articles']))}")
    print(f"平均刑期: {stats['avg_sentence_months']:.1f} 个月")
    
    dist = stats.get('sentence_distribution', {})
    if dist:
        print("刑期分布:")
        for rng, cnt in sorted(dist.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {rng}: {cnt} 案")
    
    if stats.get('typical_cases'):
        print("典型案例示例 (最多前5条):")
        for cid in stats['typical_cases'][:5]:
            print(f"  - {cid}")


def main():
    parser = ArgumentParser(description="查看 crime_type_analysis.pkl 内容")
    parser.add_argument(
        "pkl_path",
        nargs="?",
        default="data/processed/criminal/crime_type_analysis.pkl",
        help="pkl 文件路径 (默认项目相对路径)",
    )
    parser.add_argument("--crime", type=str, help="指定罪名，查看详细统计")
    parser.add_argument("--top", type=int, default=20, help="按案例数显示前 N 个罪名")
    parser.add_argument("--head", type=int, help="输出前 N 条原始记录（调试用）")
    args = parser.parse_args()

    pkl_path = Path(args.pkl_path).expanduser().resolve()
    if not pkl_path.exists():
        print(f"文件不存在: {pkl_path}")
        sys.exit(1)

    analysis = load_analysis(pkl_path)
    print(f"已加载 {len(analysis)} 种罪名\n")

    # 调试: 输出前 N 条原始记录
    if args.head:
        print(f"\n前 {args.head} 条原始记录:\n")
        for i, (crime, stats) in enumerate(list(analysis.items())[:args.head], 1):
            summary = {
                'case_count': stats['case_count'],
                'avg_sentence_months': round(stats['avg_sentence_months'], 1),
                'related_articles': stats['related_articles'][:5]  # 只显示前5条文
            }
            print(f"[{i}] {crime}: {summary}\n")
        return

    if args.crime:
        stats = analysis.get(args.crime)
        if not stats:
            print(f"未找到罪名: {args.crime}")
            sys.exit(0)
        show_crime_detail(args.crime, stats)
        return

    # 默认输出 Top N
    top_n = args.top
    print(f"案例数 Top{top_n} 罪名:")
    for crime, stats in sorted(analysis.items(), key=lambda x: x[1]['case_count'], reverse=True)[:top_n]:
        print(f"  {crime}: {stats['case_count']} 案; 平均刑期 {stats['avg_sentence_months']:.1f} 个月")


if __name__ == "__main__":
    main()
