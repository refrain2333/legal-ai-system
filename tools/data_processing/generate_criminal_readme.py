#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动生成 data/processed/criminal/README.md
包含：
1. 各 pkl 文件简要结构说明
2. 每个 pkl 文件前 5 条记录的精简展示
"""

import sys
import pickle
from pathlib import Path
from textwrap import shorten
from dataclasses import asdict, is_dataclass

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

PKL_FILES = [
    ("article_case_mappings.pkl", "dict[int, CriminalMapping]"),
    ("criminal_articles.pkl", "List[CriminalLawArticle]"),
    ("criminal_cases.pkl", "List[CriminalCase]"),
    ("crime_type_analysis.pkl", "dict[str, Dict]"),
    ("criminal_professional_dictionary.pkl", "Dict (专业词典)")
]

CRIMINAL_DIR = Path("data/processed/criminal").resolve()
README_PATH = CRIMINAL_DIR / "README.md"


def preview(obj):
    """返回对象的简短字符串表示"""
    if is_dataclass(obj):
        d = asdict(obj)
    else:
        d = obj
    return shorten(repr(d), width=120, placeholder="…")


def main():
    lines = ["# processed/criminal 目录文件概览 (自动生成)", ""]

    for filename, structure in PKL_FILES:
        pkl_path = CRIMINAL_DIR / filename
        if not pkl_path.exists():
            lines.append(f"## {filename}\n文件不存在，跳过\n")
            continue

        with open(pkl_path, "rb") as f:
            data = pickle.load(f)

        # 生成结构说明
        lines.append(f"## {filename}")
        lines.append(f"* 结构：`{structure}`")
        # 统计大小
        if isinstance(data, dict):
            total = len(data)
        else:
            total = len(data)
        lines.append(f"* 记录数：{total}")
        lines.append("")
        lines.append("前 5 条示例：")
        lines.append("```")
        # 提取前5
        if isinstance(data, dict):
            items = list(data.items())[:5]
            for k, v in items:
                lines.append(f"{k}: {preview(v)}")
        else:
            for obj in data[:5]:
                lines.append(preview(obj))
        lines.append("````\n")

    README_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"README 已生成: {README_PATH}")


if __name__ == "__main__":
    main()
