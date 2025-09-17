
"""
查看 article_case_mappings.pkl 内容的辅助脚本

用法::
    python view_article_case_mappings.py [pkl_path] [--article N] [--top K]

功能:
    1. 读取並解析 CriminalMapping 映射字典 (article_number -> CriminalMapping).
    2. 若指定 --article, 输出该法条号的详细信息。
    3. 否则按案例数量降序输出前 K 条映射统计，以快速确认数据是否符合预期。
"""

import sys
import pickle
from pathlib import Path
from typing import Dict
from argparse import ArgumentParser

# 将项目根目录加入 sys.path，确保可以导入 src 包
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.criminal_law_processor import CriminalMapping  # noqa: E402


def load_mappings(pkl_path: Path) -> Dict[int, CriminalMapping]:
    """加载并返回法条-案例映射字典"""
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    if not isinstance(data, dict):
        raise ValueError("数据格式异常，预期为 dict[int, CriminalMapping]")
    return data


def show_article_detail(mapping: CriminalMapping):
    """打印单条法条映射详细信息"""
    print(f"第 {mapping.article_number} 条 - 关联案例数: {mapping.case_count}")
    print(f"涉及罪名: {', '.join(mapping.crime_types) if mapping.crime_types else '无'}")

    # 量刑区间
    if mapping.sentencing_range:
        impr = mapping.sentencing_range.get("imprisonment", {})
        if impr:
            print(
                f"刑期范围: {impr.get('min_months')} - {impr.get('max_months')} 个月; "
                f"平均 {impr.get('avg_months'):.1f} 个月"
            )

    # 典型案例
    if mapping.typical_cases:
        print("典型案例示例 (最多前5条):")
        for cid in mapping.typical_cases[:5]:
            print(f"  - {cid}")


def main():
    parser = ArgumentParser(description="查看 article_case_mappings.pkl 内容")
    parser.add_argument(
        "pkl_path",
        nargs="?",
        default="data/processed/criminal/article_case_mappings.pkl",
        help="pkl 文件路径 (默认项目相对路径)",
    )
    parser.add_argument("--article", type=int, help="指定法条号，查看详细映射")
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="按案例数量显示前 N 条 (当未指定 --article 时有效)",
    )
    args = parser.parse_args()

    pkl_path = Path(args.pkl_path).expanduser().resolve()
    if not pkl_path.exists():
        print(f"文件不存在: {pkl_path}")
        sys.exit(1)

    mappings = load_mappings(pkl_path)
    print("人文科技")
    print(f"已加载 {len(mappings)} 条法条映射\n")

    if args.article:
        mapping = mappings.get(args.article)
        if not mapping:
            print(f"未找到第 {args.article} 条的映射")
            sys.exit(0)
        show_article_detail(mapping)
        return

    # 默认输出 Top N
    top_n = args.top
    print(f"案例数 Top{top_n} 法条:")
    for mapping in sorted(mappings.values(), key=lambda m: m.case_count, reverse=True)[:top_n]:
        print(
            f"  第{mapping.article_number}条: {mapping.case_count} 个案例; "
            f"涉罪名 {len(mapping.crime_types)} 个"
        )


if __name__ == "__main__":
    main()
