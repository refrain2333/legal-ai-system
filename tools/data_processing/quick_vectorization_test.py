#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
刑事数据向量化处理器 - 快速验证版本
处理少量数据进行快速验证
"""

import sys
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import time
from sentence_transformers import SentenceTransformer

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def quick_vectorization_test():
    """快速向量化验证"""
    print("=" * 60)
    print("刑事数据向量化 - 快速验证")
    print("=" * 60)
    
    # 1. 加载模型
    print("加载text2vec-base-chinese模型...")
    model = SentenceTransformer("shibing624/text2vec-base-chinese")
    print(f"模型维度: {model.get_sentence_embedding_dimension()}")
    
    # 2. 加载少量数据进行测试
    print("\n加载刑事数据样本...")
    data_dir = Path("data/processed/criminal")
    
    # 加载条文数据
    with open(data_dir / "criminal_articles.pkl", 'rb') as f:
        articles = pickle.load(f)
    print(f"条文总数: {len(articles)}")
    
    # 加载案例数据（仅前100个）
    with open(data_dir / "criminal_cases.pkl", 'rb') as f:
        cases = pickle.load(f)[:100]  # 只取前100个
    print(f"案例样本数: {len(cases)}")
    
    # 3. 准备文本
    print("\n准备向量化文本...")
    
    # 条文文本
    article_texts = []
    for article in articles:
        if hasattr(article, 'title') and hasattr(article, 'content'):
            text = f"{article.title}\n{article.content}"
        else:
            text = article.get('title', '') + '\n' + article.get('content', '')
        article_texts.append(text.strip())
    
    # 案例文本（只处理前100个）
    case_texts = []
    for case in cases:
        if hasattr(case, 'fact'):
            fact = case.fact or ""
            accusations = ", ".join(case.accusations) if hasattr(case, 'accusations') and case.accusations else ""
        else:
            fact = case.get('fact', '')
            accusations = ", ".join(case.get('accusations', []))
        
        text = f"{fact}\n罪名: {accusations}" if accusations else fact
        if text.strip():
            case_texts.append(text.strip())
    
    print(f"准备完成 - 条文: {len(article_texts)}, 案例: {len(case_texts)}")
    
    # 4. 向量化处理
    print("\n开始向量化处理...")
    
    # 向量化条文
    print("向量化条文...")
    article_vectors = model.encode(article_texts, batch_size=32, show_progress_bar=True)
    print(f"条文向量形状: {article_vectors.shape}")
    
    # 向量化案例
    print("向量化案例...")
    case_vectors = model.encode(case_texts, batch_size=32, show_progress_bar=True)
    print(f"案例向量形状: {case_vectors.shape}")
    
    # 5. 保存结果
    print("\n保存向量化结果...")
    output_dir = Path("data/processed/criminal")
    
    # 保存条文向量
    article_data = {
        'vectors': article_vectors,
        'texts': article_texts,
        'count': len(article_texts),
        'model_name': "shibing624/text2vec-base-chinese",
        'embedding_dim': article_vectors.shape[1]
    }
    
    with open(output_dir / "articles_vectors_sample.pkl", 'wb') as f:
        pickle.dump(article_data, f)
    
    # 保存案例向量
    case_data = {
        'vectors': case_vectors,
        'texts': case_texts,
        'count': len(case_texts),
        'model_name': "shibing624/text2vec-base-chinese", 
        'embedding_dim': case_vectors.shape[1]
    }
    
    with open(output_dir / "cases_vectors_sample.pkl", 'wb') as f:
        pickle.dump(case_data, f)
    
    print("保存完成！")
    
    # 6. 验证向量质量
    print("\n向量质量验证:")
    print(f"条文向量统计:")
    print(f"  平均模长: {np.linalg.norm(article_vectors, axis=1).mean():.4f}")
    print(f"  标准差: {np.linalg.norm(article_vectors, axis=1).std():.4f}")
    
    print(f"案例向量统计:")  
    print(f"  平均模长: {np.linalg.norm(case_vectors, axis=1).mean():.4f}")
    print(f"  标准差: {np.linalg.norm(case_vectors, axis=1).std():.4f}")
    
    # 7. 简单相似度测试
    print("\n相似度测试:")
    if len(article_texts) > 0 and len(case_texts) > 0:
        # 计算第一个条文与前5个案例的相似度
        similarities = np.dot(article_vectors[0], case_vectors[:5].T)
        print(f"第一个条文与前5个案例的相似度: {similarities}")
    
    print("\n=" * 60)
    print("快速验证完成！")
    print("=" * 60)

if __name__ == "__main__":
    quick_vectorization_test()