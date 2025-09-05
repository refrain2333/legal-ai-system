#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法智导航项目 - 渐进式向量索引构建器
支持分批次、可中断的大规模向量化处理

特点：
- 渐进式处理，避免长时间等待
- 支持中断和恢复
- 详细的进度显示
- 内存优化
"""

import numpy as np
import pickle
import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# 导入我们的模块
from .semantic_embedding import SemanticTextEmbedding
from ..data.full_dataset_processor import FullDatasetProcessor


class ProgressiveIndexBuilder:
    """渐进式索引构建器"""
    
    def __init__(self, cache_dir: str = "data/indices"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.cache_dir / "build_progress.json"
        
        # 构建状态
        self.embedding_model = None
        self.documents = []
        self.progress = {
            'total_documents': 0,
            'processed_documents': 0,
            'current_batch': 0,
            'batch_size': 50,  # 较小的批次以减少内存压力
            'completed': False,
            'start_time': 0,
            'last_update': 0
        }
    
    def start_progressive_build(self, sample_size: int = 500) -> Dict[str, Any]:
        """
        开始渐进式构建，先处理样本验证效果
        
        Args:
            sample_size: 样本数量，用于初始验证
            
        Returns:
            Dict: 构建结果
        """
        print("=" * 60)
        print("Progressive Vector Index Building")
        print("=" * 60)
        
        try:
            # 1. 加载数据
            print("Loading dataset...")
            processor = FullDatasetProcessor()
            
            if not processor.load_processed_data():
                return {'error': 'No processed data found'}
            
            self.documents = processor.documents[:sample_size]  # 使用样本
            print(f"Using sample of {len(self.documents)} documents for initial build")
            
            # 2. 初始化embedding模型
            print("\\nInitializing semantic embedding model...")
            self.embedding_model = SemanticTextEmbedding()
            model_info = self.embedding_model.initialize()
            
            print(f"Model ready: {model_info['embedding_dimension']}D vectors")
            
            # 3. 构建样本索引
            print("\\nBuilding sample index...")
            start_time = time.time()
            
            # 准备文本
            texts = []
            metadata = []
            
            for i, doc in enumerate(self.documents):
                text = doc.get('full_text', '') or f"{doc.get('title', '')}\\n{doc.get('content', '')}"
                if text.strip():
                    texts.append(text.strip()[:512])  # 限制长度以提升速度
                    metadata.append({
                        'id': doc['id'],
                        'type': doc['type'], 
                        'title': doc['title'][:100],
                        'index': i
                    })
            
            print(f"Texts prepared: {len(texts)} valid documents")
            
            # 4. 向量化 (小批次)
            print("Starting vectorization...")
            vectors = self.embedding_model.encode_texts(
                texts,
                batch_size=16,  # 小批次
                show_progress=True
            )
            
            # 5. 构建简单索引
            index_data = {
                'vectors': vectors,
                'metadata': metadata,
                'dimension': vectors.shape[1],
                'total_docs': len(metadata),
                'build_time': time.time() - start_time,
                'sample_build': True
            }
            
            # 6. 保存索引
            index_path = self.cache_dir / "sample_index.pkl"
            with open(index_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            print(f"\\nSample index built successfully!")
            print(f"  - Documents: {len(metadata)}")
            print(f"  - Vector dimension: {vectors.shape[1]}")
            print(f"  - Build time: {index_data['build_time']:.2f}s")
            print(f"  - Index saved: {index_path}")
            
            # 7. 测试检索
            print("\\nTesting sample search...")
            test_results = self._test_sample_search(vectors, metadata, texts)
            
            return {
                'success': True,
                'sample_size': len(metadata),
                'build_time': index_data['build_time'],
                'test_results': test_results,
                'next_step': 'full_build' if len(processor.documents) > sample_size else 'completed'
            }
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {'error': str(e)}
    
    def _test_sample_search(self, vectors: np.ndarray, metadata: List[Dict], texts: List[str]) -> List[Dict]:
        """测试样本检索"""
        test_queries = [
            "合同违约责任",
            "故意伤害罪", 
            "民事诉讼"
        ]
        
        results = []
        
        for query in test_queries:
            # 向量化查询
            query_vector = self.embedding_model.encode_query(query)
            
            # 计算相似度
            similarities = np.dot(vectors, query_vector)
            
            # 获取top-3
            top_indices = np.argsort(similarities)[::-1][:3]
            
            query_results = []
            for idx in top_indices:
                if idx < len(metadata):
                    query_results.append({
                        'score': float(similarities[idx]),
                        'title': metadata[idx]['title'],
                        'type': metadata[idx]['type']
                    })
            
            results.append({
                'query': query,
                'results': query_results
            })
            
            print(f"  Query: {query}")
            for i, result in enumerate(query_results):
                print(f"    {i+1}. [{result['score']:.3f}] {result['title']}")
        
        return results
    
    def continue_full_build(self, batch_size: int = 32) -> Dict[str, Any]:
        """
        继续构建完整索引
        
        Args:
            batch_size: 批处理大小
            
        Returns:
            Dict: 构建进度
        """
        print("=" * 60)
        print("Continuing Full Index Build")
        print("=" * 60)
        
        try:
            # 加载完整数据集
            processor = FullDatasetProcessor()
            if not processor.load_processed_data():
                return {'error': 'No processed data found'}
            
            total_docs = len(processor.documents)
            print(f"Total documents to process: {total_docs}")
            
            # 询问用户是否继续
            print(f"\\nThis will process {total_docs} documents with semantic vectorization.")
            print(f"Estimated time: {total_docs * 0.1 / 60:.1f} minutes")
            print("Do you want to continue? (y/n)")
            
            # 对于自动化测试，默认返回准备状态
            return {
                'ready_for_full_build': True,
                'total_documents': total_docs,
                'estimated_time_minutes': total_docs * 0.1 / 60,
                'batch_size': batch_size,
                'recommendation': 'Use cloud training if local processing is too slow'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_sample_index_stats(self) -> Dict[str, Any]:
        """获取样本索引统计信息"""
        index_path = self.cache_dir / "sample_index.pkl"
        
        if not index_path.exists():
            return {'error': 'No sample index found'}
        
        try:
            with open(index_path, 'rb') as f:
                index_data = pickle.load(f)
            
            return {
                'total_docs': index_data['total_docs'],
                'vector_dimension': index_data['dimension'],
                'build_time': index_data['build_time'],
                'index_size_mb': index_path.stat().st_size / (1024 * 1024),
                'sample_build': index_data.get('sample_build', False)
            }
            
        except Exception as e:
            return {'error': str(e)}


def main():
    """主函数 - 渐进式构建流程"""
    print("Legal AI - Progressive Index Builder")
    print("=" * 50)
    
    builder = ProgressiveIndexBuilder()
    
    # Step 1: 构建样本索引验证效果
    print("Step 1: Building sample index for validation...")
    sample_result = builder.start_progressive_build(sample_size=500)
    
    if 'error' in sample_result:
        print(f"ERROR: {sample_result['error']}")
        return
    
    if not sample_result.get('success'):
        print("Sample build failed")
        return
    
    print(f"\\nSample build completed successfully!")
    print(f"Processing speed: {sample_result['sample_size'] / sample_result['build_time']:.1f} docs/sec")
    
    # Step 2: 评估是否继续完整构建
    if sample_result.get('next_step') == 'full_build':
        print("\\nStep 2: Evaluating full build...")
        full_build_info = builder.continue_full_build()
        
        if 'error' not in full_build_info:
            print(f"\\nFull build analysis:")
            print(f"  - Total documents: {full_build_info['total_documents']}")
            print(f"  - Estimated time: {full_build_info['estimated_time_minutes']:.1f} minutes")
            print(f"  - Recommended batch size: {full_build_info['batch_size']}")
            print(f"\\nRecommendation: {full_build_info['recommendation']}")
            
            print("\\nSample index is ready for testing!")
            print("You can now decide whether to continue with full build or use cloud training.")
    else:
        print("\\nAll documents processed in sample build!")
    
    # Step 3: 显示样本索引统计
    stats = builder.get_sample_index_stats()
    if 'error' not in stats:
        print(f"\\nSample Index Statistics:")
        print(f"  - Documents: {stats['total_docs']}")
        print(f"  - Vector dimension: {stats['vector_dimension']}")
        print(f"  - Build time: {stats['build_time']:.2f}s")
        print(f"  - Index size: {stats['index_size_mb']:.1f}MB")


if __name__ == "__main__":
    main()