#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看 criminal_articles.pkl 内容

用法::
    python view_criminal_articles.py [pkl_path] [--head N]
"""

import sys
import pickle
from argparse import ArgumentParser
from pathlib import Path

# 确保可以导入 src 包以正确反序列化
import sys
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dataclasses import asdict


def load_articles(pkl_path: Path):
    with open(pkl_path, 'rb') as f:
        return pickle.load(f)


def main():
    parser = ArgumentParser(description="预览 criminal_articles.pkl")
    parser.add_argument("pkl_path", nargs="?", default="data/processed/criminal/criminal_articles.pkl")
    parser.add_argument("--head", type=int, default=10, help="展示前 N 条记录")
    args = parser.parse_args()

    pkl_path = Path(args.pkl_path).resolve()
    if not pkl_path.exists():
        print(f"文件不存在: {pkl_path}")
        sys.exit(1)

    articles = load_articles(pkl_path)
    total = len(articles)
    print(f"已加载 {total} 条刑法条文\n")

    n = min(args.head, total)
    print(f"前 {n} 条记录:\n")

    for art in articles[:n]:
        # art is CriminalLawArticle dataclass;显示条文号、标题、章节
        num = art.article_number
        title = art.title
        chapter = art.chapter or ""
        print(f"第{num}条 {title} {chapter}")

if __name__ == "__main__":
    main()
