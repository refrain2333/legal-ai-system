#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法智导航项目 - 完整版向量索引系统
支持大规模数据的高性能向量检索

与simple_index.py的区别：
- 支持3500+文档的大规模索引
- 使用sentence-transformers语义向量化
- 内存优化和批量处理
- 支持索引缓存和增量更新
- 可选的Faiss高性能索引

作者：Claude Code Assistant
版本：v0.3.0 (完整版)
"""

import numpy as np
import pickle
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

# 导入我们的模块
from .semantic_embedding import SemanticTextEmbedding
from ..data.full_dataset_processor import FullDatasetProcessor


class LargeScaleVectorIndex:
    """
    大规模向量索引系统
    
    特点：
    - 支持3500+文档的高效索引
    - 语义向量检索 (768维)
    - 批量向量化处理
    - 索引持久化和缓存
    - 内存优化设计
    """
    
    def __init__(self, embedding_model: Optional[SemanticTextEmbedding] = None,
                 cache_dir: str = "data/indices"):
        """
        初始化大规模向量索引
        
        Args:
            embedding_model: 语义向量化模型
            cache_dir: 索引缓存目录
        """
        self.embedding_model = embedding_model or SemanticTextEmbedding()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 索引数据
        self.document_vectors = None
        self.document_metadata = []
        self.vector_dimension = 768  # sentence-transformers固定维度
        
        # 索引状态
        self.is_built = False
        self.total_documents = 0
        
        # 性能统计
        self.stats = {
            'index_build_time': 0.0,
            'vectorization_time': 0.0,
            'total_documents': 0,
            'index_size_mb': 0.0,
            'average_search_time': 0.0,
            'total_searches': 0
        }
    
    def build_index(self, documents: List[Dict[str, Any]], 
                   batch_size: int = 64, 
                   use_cache: bool = True) -> Dict[str, Any]:
        """
        构建向量索引
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 构建统计信息
        """
        print("=" * 60)
        print("Building Large-Scale Vector Index")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. 检查缓存
            if use_cache and self.load_index_cache():
                print("Index loaded from cache successfully!")
                return self.get_build_stats()
            
            # 2. 初始化embedding模型
            if not self.embedding_model.is_initialized:
                self.embedding_model.initialize()
            
            # 3. 准备文档文本
            print(f"Preparing {len(documents)} documents for vectorization...")
            texts = []
            metadata = []
            
            for doc in documents:
                # 使用full_text作为向量化输入
                text = doc.get('full_text', '') or f"{doc.get('title', '')}\\n{doc.get('content', '')}"
                if text.strip():
                    texts.append(text.strip())
                    metadata.append({
                        'id': doc['id'],
                        'type': doc['type'],
                        'title': doc['title'],
                        'source': doc.get('metadata', {}).get('source', 'unknown')
                    })
            
            print(f"  - Valid documents: {len(texts)}")
            
            # 4. 批量向量化
            print("Starting batch vectorization...")
            vectorization_start = time.time()
            
            # 分批处理以优化内存使用
            all_vectors = []
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(texts))
                batch_texts = texts[start_idx:end_idx]
                
                print(f"  - Processing batch {batch_idx + 1}/{total_batches} ({len(batch_texts)} texts)")
                
                # 向量化当前批次
                batch_vectors = self.embedding_model.encode_texts(
                    batch_texts, 
                    batch_size=min(batch_size, 32),  # 控制内存使用
                    show_progress=False  # 避免嵌套进度条
                )
                all_vectors.append(batch_vectors)
            
            # 5. 合并所有向量
            self.document_vectors = np.vstack(all_vectors)
            self.document_metadata = metadata
            self.total_documents = len(metadata)
            
            vectorization_time = time.time() - vectorization_start
            
            # 6. 构建索引结构
            print("Building index structure...")
            self._build_index_structure()
            
            # 7. 更新统计信息
            build_time = time.time() - start_time
            index_size_mb = self._calculate_index_size()
            
            self.stats.update({
                'index_build_time': build_time,
                'vectorization_time': vectorization_time,
                'total_documents': self.total_documents,
                'index_size_mb': index_size_mb
            })
            
            self.is_built = True
            
            print(f"\\nIndex building completed!")
            print(f"  - Total documents: {self.total_documents}")
            print(f"  - Vector dimension: {self.vector_dimension}")
            print(f"  - Index size: {index_size_mb:.1f}MB")
            print(f"  - Build time: {build_time:.2f}s")
            print(f"  - Vectorization time: {vectorization_time:.2f}s")
            
            # 8. 保存缓存
            if use_cache:
                self.save_index_cache()
            
            return self.get_build_stats()
            
        except Exception as e:
            print(f"ERROR building index: {str(e)}")
            raise
    
    def _build_index_structure(self):
        """构建索引结构（为可能的Faiss升级预留接口）"""
        # 当前使用简单的numpy数组结构
        # 可以后续升级为Faiss索引
        
        # 验证向量维度
        if self.document_vectors.shape[1] != self.vector_dimension:
            print(f"WARNING: Vector dimension mismatch: {self.document_vectors.shape[1]} vs {self.vector_dimension}")
            self.vector_dimension = self.document_vectors.shape[1]
        
        # 归一化向量（提升余弦相似度计算效率）
        norms = np.linalg.norm(self.document_vectors, axis=1, keepdims=True)
        self.document_vectors = self.document_vectors / np.maximum(norms, 1e-8)
        
        print(f"  - Index structure built: {self.document_vectors.shape}")
    
    def search(self, query: str, top_k: int = 10, 
              min_similarity: float = 0.0, 
              doc_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        向量语义检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            doc_types: 过滤的文档类型
            
        Returns:
            List[Dict]: 检索结果列表
        """
        if not self.is_built:
            raise ValueError("Index not built. Please call build_index() first.")
        
        search_start = time.time()
        
        try:
            # 1. 向量化查询
            query_vector = self.embedding_model.encode_query(query)
            
            # 2. 计算相似度
            similarities = np.dot(self.document_vectors, query_vector)
            
            # 3. 应用过滤条件
            valid_indices = np.where(similarities >= min_similarity)[0]
            
            if doc_types:
                # 按文档类型过滤
                type_mask = np.array([
                    self.document_metadata[i]['type'] in doc_types 
                    for i in valid_indices
                ])
                valid_indices = valid_indices[type_mask]
            
            # 4. 排序并获取top-k
            if len(valid_indices) == 0:
                return []
            
            valid_similarities = similarities[valid_indices]
            sorted_indices = valid_indices[np.argsort(valid_similarities)[::-1]]
            top_indices = sorted_indices[:top_k]
            
            # 5. 构建结果
            results = []
            for idx in top_indices:
                metadata = self.document_metadata[idx]
                similarity = float(similarities[idx])
                
                result = {
                    'id': metadata['id'],
                    'type': metadata['type'],
                    'title': metadata['title'],
                    'score': similarity,
                    'source': metadata['source']
                }
                results.append(result)
            
            # 6. 更新搜索统计
            search_time = time.time() - search_start
            self.stats['total_searches'] += 1
            self.stats['average_search_time'] = (
                (self.stats['average_search_time'] * (self.stats['total_searches'] - 1) + search_time)
                / self.stats['total_searches']
            )
            
            return results
            
        except Exception as e:
            print(f"ERROR during search: {str(e)}")
            raise
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档详情
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Dict: 文档信息，如果未找到则返回None
        """
        for i, metadata in enumerate(self.document_metadata):
            if metadata['id'] == doc_id:
                return {
                    **metadata,
                    'index': i,
                    'vector_norm': float(np.linalg.norm(self.document_vectors[i]))
                }
        return None
    
    def _calculate_index_size(self) -> float:
        """计算索引占用的内存大小 (MB)"""
        if self.document_vectors is None:
            return 0.0
        
        # 向量数据大小
        vector_size = self.document_vectors.nbytes
        
        # 元数据大小（估算）
        metadata_size = len(str(self.document_metadata).encode('utf-8'))
        
        total_size = vector_size + metadata_size
        return total_size / (1024 * 1024)
    
    def save_index_cache(self, cache_name: str = "large_scale_index.pkl") -> str:
        """
        保存索引缓存
        
        Args:
            cache_name: 缓存文件名
            
        Returns:
            str: 缓存文件路径
        """
        if not self.is_built:
            raise ValueError("Index not built, cannot save cache")
        
        cache_path = self.cache_dir / cache_name
        
        try:
            cache_data = {
                'document_vectors': self.document_vectors,
                'document_metadata': self.document_metadata,
                'vector_dimension': self.vector_dimension,
                'total_documents': self.total_documents,
                'stats': self.stats,
                'version': '0.3.0',
                'created_at': time.time()
            }
            
            print(f"Saving index cache to {cache_path}...")
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            cache_size = cache_path.stat().st_size / (1024 * 1024)
            
            print(f"  - Index cache saved: {cache_size:.1f}MB")
            
            return str(cache_path)
            
        except Exception as e:
            print(f"ERROR saving index cache: {str(e)}")
            raise
    
    def load_index_cache(self, cache_name: str = "large_scale_index.pkl") -> bool:
        """
        加载索引缓存
        
        Args:
            cache_name: 缓存文件名
            
        Returns:
            bool: 加载是否成功
        """
        cache_path = self.cache_dir / cache_name
        
        if not cache_path.exists():
            return False
        
        try:
            print(f"Loading index cache from {cache_path}...")
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.document_vectors = cache_data.get('document_vectors')
            self.document_metadata = cache_data.get('document_metadata', [])
            self.vector_dimension = cache_data.get('vector_dimension', 768)
            self.total_documents = cache_data.get('total_documents', 0)
            self.stats = cache_data.get('stats', {})
            
            self.is_built = (
                self.document_vectors is not None and 
                len(self.document_metadata) > 0
            )
            
            cache_size = cache_path.stat().st_size / (1024 * 1024)
            
            print(f"  - Index cache loaded: {self.total_documents} documents, {cache_size:.1f}MB")
            
            return True
            
        except Exception as e:
            print(f"ERROR loading index cache: {str(e)}")
            return False
    
    def get_build_stats(self) -> Dict[str, Any]:
        """获取索引构建统计信息"""
        return {
            **self.stats,
            'is_built': self.is_built,
            'total_documents': self.total_documents,
            'vector_dimension': self.vector_dimension
        }


def test_large_scale_index():
    """测试大规模向量索引系统"""
    print("=" * 60)
    print("Large-Scale Vector Index Test")
    print("=" * 60)
    
    try:
        # 1. 加载完整数据集
        print("Loading full dataset...")
        processor = FullDatasetProcessor()
        
        if not processor.load_processed_data():
            print("No processed data found, processing raw data...")
            documents = processor.process_all_documents()
            processor.save_processed_data()
        else:
            documents = processor.documents
        
        print(f"Dataset loaded: {len(documents)} documents")
        
        # 2. 创建语义embedding模型
        print("\\nInitializing semantic embedding model...")
        embedding_model = SemanticTextEmbedding()
        
        # 3. 创建大规模索引
        print("\\nCreating large-scale vector index...")
        index = LargeScaleVectorIndex(embedding_model)
        
        # 4. 构建索引
        print("\\nBuilding vector index...")
        build_stats = index.build_index(documents, batch_size=64)
        
        # 5. 测试检索
        print("\\nTesting semantic search...")
        test_queries = [
            "合同违约责任",
            "故意伤害罪",
            "民事诉讼程序",
            "交通事故处理"
        ]
        
        for query in test_queries:
            print(f"\\nQuery: {query}")
            results = index.search(query, top_k=3, min_similarity=0.3)
            
            for i, result in enumerate(results):
                print(f"  {i+1}. [{result['score']:.3f}] [{result['type']}] {result['title'][:50]}...")
        
        # 6. 显示统计信息
        print("\\nIndex Statistics:")
        stats = index.get_build_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  - {key}: {value:.3f}")
            else:
                print(f"  - {key}: {value}")
        
        print("\\nLarge-scale index test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\\nTest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_large_scale_index()
    
    if success:
        print("\\nReady to upgrade retrieval service!")
    else:
        print("\\nNeed to fix indexing issues")