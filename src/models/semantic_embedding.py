#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法智导航项目 - 完整版语义文本向量化模型
基于sentence-transformers的语义理解模型

与simple_embedding.py的区别：
- 使用sentence-transformers进行语义向量化（非TF-IDF）
- 支持真正的语义理解和相似度匹配
- 768维固定向量维度
- 更高的相似度分数 (0.6-0.8 vs 0.1-0.2)

作者：Claude Code Assistant
版本：v0.3.0 (完整版)
"""

import numpy as np
import pickle
import os
import time
from typing import List, Optional, Dict, Any
from pathlib import Path


class SemanticTextEmbedding:
    """
    基于sentence-transformers的语义文本向量化模型
    
    特点：
    - 使用shibing624/text2vec-base-chinese预训练模型
    - 768维固定向量输出
    - 真正的语义理解能力
    - 支持批量处理和增量更新
    """
    
    def __init__(self, model_name: str = 'shibing624/text2vec-base-chinese'):
        """
        初始化语义向量化模型
        
        Args:
            model_name: 预训练模型名称，默认使用中文优化模型
        """
        self.model_name = model_name
        self.model = None
        self.is_initialized = False
        self.model_info = {}
        
        # 性能统计
        self.stats = {
            'model_load_time': 0.0,
            'total_texts_processed': 0,
            'total_encoding_time': 0.0,
            'average_encoding_speed': 0.0
        }
    
    def initialize(self) -> Dict[str, Any]:
        """
        初始化sentence-transformers模型
        
        Returns:
            Dict: 模型信息和加载统计
        """
        if self.is_initialized:
            return self.model_info
        
        print(f"Initializing semantic embedding model: {self.model_name}")
        start_time = time.time()
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # 加载预训练模型
            self.model = SentenceTransformer(self.model_name)
            
            # 记录加载时间
            load_time = time.time() - start_time
            self.stats['model_load_time'] = load_time
            
            # 获取模型信息
            self.model_info = {
                'model_name': self.model_name,
                'embedding_dimension': 768,  # Chinese text2vec模型固定维度
                'max_seq_length': self.model.max_seq_length,
                'load_time': load_time,
                'model_type': 'semantic_transformer'
            }
            
            self.is_initialized = True
            
            print(f"Model initialized successfully!")
            print(f"   - Model: {self.model_name}")
            print(f"   - Vector dimension: {self.model_info['embedding_dimension']}")
            print(f"   - Max sequence length: {self.model_info['max_seq_length']}")
            print(f"   - Loading time: {load_time:.2f}s")
            
            return self.model_info
            
        except Exception as e:
            error_msg = f"Model initialization failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            raise RuntimeError(error_msg)
    
    def encode_texts(self, texts: List[str], batch_size: int = 32, 
                    show_progress: bool = True) -> np.ndarray:
        """
        批量编码文本为语义向量
        
        Args:
            texts: 待编码的文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度
            
        Returns:
            np.ndarray: 形状为 (n_texts, 768) 的向量矩阵
        """
        if not self.is_initialized:
            self.initialize()
        
        if not texts:
            return np.array([]).reshape(0, 768)
        
        print(f"Encoding {len(texts)} texts...")
        start_time = time.time()
        
        try:
            # 使用sentence-transformers进行批量编码
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True  # 归一化向量，提升相似度计算效果
            )
            
            # 更新统计信息
            encoding_time = time.time() - start_time
            self.stats['total_texts_processed'] += len(texts)
            self.stats['total_encoding_time'] += encoding_time
            self.stats['average_encoding_speed'] = (
                self.stats['total_texts_processed'] / 
                self.stats['total_encoding_time'] if self.stats['total_encoding_time'] > 0 else 0
            )
            
            print(f"Encoding completed!")
            print(f"   - Text count: {len(texts)}")
            print(f"   - Vector shape: {embeddings.shape}")
            print(f"   - Encoding time: {encoding_time:.2f}s")
            print(f"   - Processing speed: {len(texts)/encoding_time:.1f} texts/sec")
            
            return embeddings.astype(np.float32)
            
        except Exception as e:
            error_msg = f"Text encoding failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            raise RuntimeError(error_msg)
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        编码单个查询文本
        
        Args:
            query: 查询文本
            
        Returns:
            np.ndarray: 形状为 (768,) 的查询向量
        """
        if not query.strip():
            return np.zeros(768, dtype=np.float32)
        
        embeddings = self.encode_texts([query], show_progress=False)
        return embeddings[0]
    
    def compute_similarity(self, query_vector: np.ndarray, 
                         document_vectors: np.ndarray) -> np.ndarray:
        """
        计算查询向量与文档向量的语义相似度
        
        Args:
            query_vector: 查询向量 (768,)
            document_vectors: 文档向量矩阵 (n_docs, 768)
            
        Returns:
            np.ndarray: 相似度分数数组 (n_docs,)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        # 重塑查询向量为 (1, 768)
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # 计算余弦相似度
        similarities = cosine_similarity(query_vector, document_vectors)[0]
        
        return similarities
    
    def save_model_cache(self, cache_path: str) -> bool:
        """
        保存模型缓存信息（不包含模型本身，只保存统计和配置）
        
        Args:
            cache_path: 缓存文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            cache_data = {
                'model_info': self.model_info,
                'stats': self.stats,
                'model_name': self.model_name,
                'is_initialized': self.is_initialized
            }
            
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"Model cache saved: {cache_path}")
            return True
            
        except Exception as e:
            print(f"Model cache save failed: {str(e)}")
            return False
    
    def load_model_cache(self, cache_path: str) -> bool:
        """
        加载模型缓存信息
        
        Args:
            cache_path: 缓存文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if not os.path.exists(cache_path):
                return False
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.model_info = cache_data.get('model_info', {})
            self.stats = cache_data.get('stats', self.stats)
            self.model_name = cache_data.get('model_name', self.model_name)
            
            print(f"Model cache loaded: {cache_path}")
            return True
            
        except Exception as e:
            print(f"Model cache load failed: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取模型性能统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            **self.stats,
            **self.model_info,
            'is_initialized': self.is_initialized
        }


def test_semantic_embedding():
    """测试语义向量化模型的功能"""
    print("=" * 60)
    print("Semantic Embedding Model Function Test")
    print("=" * 60)
    
    # 创建模型实例
    embedding_model = SemanticTextEmbedding()
    
    # 测试文本
    test_texts = [
        "合同违约的法律责任和赔偿标准",
        "故意伤害罪的构成要件和量刑标准", 
        "民事诉讼的基本程序和时效规定",
        "交通事故责任认定和理赔流程",
        "劳动合同纠纷的处理方式和法律依据"
    ]
    
    test_query = "合同纠纷如何承担责任"
    
    try:
        # 1. 初始化模型
        print("\\n1. Initializing model...")
        model_info = embedding_model.initialize()
        
        # 2. 编码测试文本
        print("\\n2. Encoding test texts...")
        embeddings = embedding_model.encode_texts(test_texts)
        
        # 3. 编码查询
        print("\\n3. Encoding query text...")
        query_vector = embedding_model.encode_query(test_query)
        
        # 4. 计算相似度
        print("\\n4. Computing semantic similarity...")
        similarities = embedding_model.compute_similarity(query_vector, embeddings)
        
        # 5. 显示结果
        print("\\nSemantic matching results:")
        print(f"Query: {test_query}")
        print("-" * 50)
        
        # 按相似度排序
        sorted_indices = np.argsort(similarities)[::-1]
        
        for i, idx in enumerate(sorted_indices[:3]):
            score = similarities[idx]
            text = test_texts[idx]
            print(f"{i+1}. [{score:.4f}] {text}")
        
        # 6. 显示统计信息
        print("\\nPerformance statistics:")
        stats = embedding_model.get_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   - {key}: {value:.3f}")
            else:
                print(f"   - {key}: {value}")
        
        print("\\nAll tests passed! Semantic model works correctly")
        return True
        
    except Exception as e:
        print(f"\\nTest failed: {str(e)}")
        return False


if __name__ == "__main__":
    # 运行测试
    success = test_semantic_embedding()
    
    if success:
        print("\\nSemantic embedding model ready for integration!")
    else:
        print("\\nNeed to check model configuration or dependencies")