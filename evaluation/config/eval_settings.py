#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估配置文件
定义评估参数和设置
"""

import os
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data" / "processed"
CRIMINAL_DATA_DIR = DATA_DIR / "criminal"
VECTORS_DATA_DIR = DATA_DIR / "vectors"
RESULTS_DIR = BASE_DIR / "results"

# 确保结果目录存在
RESULTS_DIR.mkdir(exist_ok=True)

# 数据文件路径
ARTICLE_CASE_MAPPINGS_PATH = CRIMINAL_DATA_DIR / "article_case_mappings.pkl"
CRIMINAL_ARTICLES_PATH = CRIMINAL_DATA_DIR / "criminal_articles.pkl"
CRIMINAL_CASES_PATH = CRIMINAL_DATA_DIR / "criminal_cases.pkl"
CRIME_TYPES_PATH = BASE_DIR.parent / "data" / "cases" / "crime.txt"

# 评估参数
EVALUATION_CONFIG = {
    # 检索参数
    "top_k_values": [1, 3, 5, 10, 20],  # 评估不同K值的性能
    "default_top_k": 10,  # 默认返回结果数

    # 测试集参数
    "test_sample_size": 30,   # 法条↔案例搜索测试样本数量
    "crime_consistency_sample_size": 32,  # 罪名一致性评估样本数量

    # 快速评估模式参数（--quick选项）
    "quick_test_sample_size": 20,  # 快速模式测试样本数
    "quick_crime_consistency_size": 20,  # 快速模式罪名一致性样本数

    "random_seed": 42,  # 随机种子
    "test_query_types": [
        "article_to_cases",  # 法条搜索相关案例
        "case_to_articles",  # 案例搜索相关法条
        "crime_keywords",    # 罪名关键词搜索
        "mixed_search"       # 混合搜索测试
    ],
    
    # 评估指标
    "metrics": [
        "precision",
        "recall", 
        "f1_score",
        "map",  # Mean Average Precision
        "ndcg", # Normalized Discounted Cumulative Gain
        "mrr",  # Mean Reciprocal Rank
    ],
    
    # 语义相关性阈值
    "similarity_thresholds": [0.3, 0.4, 0.5, 0.6, 0.7],
    "default_threshold": 0.4,
    
    # 报告设置
    "report_formats": ["text", "json", "html"],
    "include_error_analysis": True,
    "include_visualizations": True,
    
    # 性能设置
    "batch_size": 10,  # 批处理大小
    "use_cache": True,  # 是否使用缓存
    "max_workers": 4,   # 并发工作线程数
}

# 评估权重（用于计算综合得分）
METRIC_WEIGHTS = {
    "precision": 0.25,
    "recall": 0.25,
    "f1_score": 0.20,
    "map": 0.15,
    "ndcg": 0.10,
    "mrr": 0.05,
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": RESULTS_DIR / "evaluation.log",
}

# 可视化配置
VISUALIZATION_CONFIG = {
    "figure_size": (10, 6),
    "dpi": 100,
    "style": "seaborn",
    "save_figures": True,
    "figure_format": "png"
}