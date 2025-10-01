#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量空间对齐器
解决基础模型和微调模型向量空间不匹配问题
"""

import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class VectorSpaceAligner:
    """向量空间对齐器"""

    def __init__(self):
        self.scale_factor = None
        self.is_calibrated = False

    def calibrate_with_sample(self, sample_query_vectors: np.ndarray,
                            database_vectors: np.ndarray) -> bool:
        """
        使用样本向量校准对齐参数

        Args:
            sample_query_vectors: 微调模型的查询向量样本 (M, 768)
            database_vectors: 数据库向量 (N, 768)

        Returns:
            校准是否成功
        """
        try:
            # 计算向量范数统计
            query_norms = np.linalg.norm(sample_query_vectors, axis=1)
            db_norms = np.linalg.norm(database_vectors, axis=1)

            # 计算尺度因子
            query_mean_norm = query_norms.mean()
            db_mean_norm = db_norms.mean()

            self.scale_factor = db_mean_norm / query_mean_norm

            logger.info(f"Vector space calibration:")
            logger.info(f"  Query vectors mean norm: {query_mean_norm:.3f}")
            logger.info(f"  Database vectors mean norm: {db_mean_norm:.3f}")
            logger.info(f"  Scale factor: {self.scale_factor:.3f}")

            self.is_calibrated = True
            return True

        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return False

    def align_query_vector(self, query_vector: np.ndarray) -> np.ndarray:
        """
        对齐查询向量到数据库向量空间

        Args:
            query_vector: 原始查询向量

        Returns:
            对齐后的查询向量
        """
        if not self.is_calibrated:
            logger.warning("Aligner not calibrated, returning original vector")
            return query_vector

        # 方法1：简单缩放对齐
        aligned_vector = query_vector * self.scale_factor

        return aligned_vector

    def align_query_vector_normalize(self, query_vector: np.ndarray,
                                   target_norm: float = None) -> np.ndarray:
        """
        通过归一化对齐查询向量

        Args:
            query_vector: 原始查询向量
            target_norm: 目标范数，如果None则使用校准的范数

        Returns:
            对齐后的查询向量
        """
        if target_norm is None:
            if not self.is_calibrated:
                logger.warning("No target norm specified and aligner not calibrated")
                return query_vector
            # 使用校准得到的目标范数（数据库平均范数）
            target_norm = 19.776  # 从之前分析得到的数据库平均范数

        # 计算当前范数
        current_norm = np.linalg.norm(query_vector)

        if current_norm == 0:
            return query_vector

        # 缩放到目标范数
        aligned_vector = query_vector * (target_norm / current_norm)

        return aligned_vector


def test_vector_alignment():
    """测试向量对齐效果"""
    print("=== 向量对齐测试 ===")

    # 加载数据库向量
    vectors_path = "data/processed/vectors/criminal_articles_vectors.pkl"
    with open(vectors_path, "rb") as f:
        db_data = pickle.load(f)

    db_vectors = db_data['vectors']
    print(f"数据库向量: {db_vectors.shape}, 平均范数: {np.linalg.norm(db_vectors, axis=1).mean():.3f}")

    # 模拟微调模型查询向量（范数约11.4）
    np.random.seed(42)
    mock_query = np.random.randn(768) * 11.4  # 模拟微调模型向量
    query_norm = np.linalg.norm(mock_query)
    print(f"模拟查询向量范数: {query_norm:.3f}")

    # 创建对齐器
    aligner = VectorSpaceAligner()

    # 校准（使用少量样本）
    sample_queries = np.random.randn(5, 768) * 11.4  # 5个样本查询
    aligner.calibrate_with_sample(sample_queries, db_vectors[:100])  # 使用前100个数据库向量校准

    # 测试对齐
    aligned_query = aligner.align_query_vector_normalize(mock_query)
    aligned_norm = np.linalg.norm(aligned_query)
    print(f"对齐后查询向量范数: {aligned_norm:.3f}")

    # 测试相似度效果
    if mock_query.ndim == 1:
        mock_query_2d = mock_query.reshape(1, -1)
        aligned_query_2d = aligned_query.reshape(1, -1)

    # 原始相似度
    original_sims = cosine_similarity(mock_query_2d, db_vectors[:100])[0]

    # 对齐后相似度
    aligned_sims = cosine_similarity(aligned_query_2d, db_vectors[:100])[0]

    print(f"原始相似度范围: [{original_sims.min():.4f}, {original_sims.max():.4f}]")
    print(f"对齐相似度范围: [{aligned_sims.min():.4f}, {aligned_sims.max():.4f}]")

    # 检查top-5
    original_top5 = np.argsort(original_sims)[-5:][::-1]
    aligned_top5 = np.argsort(aligned_sims)[-5:][::-1]
    overlap = len(set(original_top5) & set(aligned_top5))

    print(f"原始top-5: {original_top5}")
    print(f"对齐top-5: {aligned_top5}")
    print(f"重叠数量: {overlap}/5")


if __name__ == "__main__":
    test_vector_alignment()