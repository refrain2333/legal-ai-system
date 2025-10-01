#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速向量化测试工具
用于快速测试Lawformer模型的向量化效果
"""

import sys
import numpy as np
from pathlib import Path
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入Lawformer嵌入器
from src.infrastructure.storage.lawformer_embedder import LawformerEmbedder


def run_quick_test():
    """运行快速向量化测试"""
    
    print("=" * 60)
    print("Lawformer 快速向量化测试")
    print("=" * 60)
    
    # 测试文本
    test_texts = [
        "李某犯抢劫罪，被判有期徒刑三年",
        "以暴力、胁迫或者其他方法抢劫公私财物的，处三年以上十年以下有期徒刑",
        "盗窃公私财物，数额较大的，或者多次盗窃、入户盗窃、携带凶器盗窃、扒窃的",
        "王某因故意伤害他人身体，造成轻伤二级"
    ]
    
    try:
        print("加载Lawformer模型...")
        model = LawformerEmbedder(model_name="thunlp/Lawformer")
        print("模型加载成功！")
        
        print(f"模型维度: {model.get_sentence_embedding_dimension()}")
        
        # 向量化测试
        print("\n开始向量化测试...")
        start_time = time.time()
        
        embeddings = model.encode(test_texts, show_progress_bar=True)
        
        end_time = time.time()
        
        print(f"\n向量化完成！")
        print(f"处理时间: {end_time - start_time:.2f}秒")
        print(f"文本数量: {len(test_texts)}")
        print(f"向量形状: {embeddings.shape}")
        print(f"向量类型: {embeddings.dtype}")
        
        # 简单相似度测试
        print("\n相似度测试:")
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(embeddings)
        
        for i, text1 in enumerate(test_texts):
            for j, text2 in enumerate(test_texts):
                if i < j:
                    sim = similarities[i][j]
                    print(f"文本{i+1} vs 文本{j+1}: {sim:.4f}")
        
        print("\n=" * 60)
        print("测试完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_quick_test()
    sys.exit(0 if success else 1)