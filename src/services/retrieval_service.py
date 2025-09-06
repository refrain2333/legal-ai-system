#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法智导航项目 - 升级版检索服务 (v0.3.0)
集成完整语义检索功能 - 3,519个文档的语义向量化
"""

import asyncio
import numpy as np
import pickle
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading
from ..models.semantic_embedding import SemanticTextEmbedding

class RetrievalService:
    """升级版检索服务 - 完全向后兼容"""
    
    def __init__(self, index_file: str = "data/indices/complete_semantic_index.pkl"):
        self.index_file = Path(index_file)
        self.embedding_model = None
        self.vectors = None
        self.metadata = []
        self.is_initialized = False
        self.init_lock = threading.Lock()
        
        # 新增：智能混合排序服务
        self.hybrid_ranking_service = None
        
        self.stats = {
            'total_documents': 0,
            'vector_dimension': 0,
            'total_searches': 0,
            'average_search_time': 0.0,
            'service_version': '0.4.0_intelligent_hybrid'
        }
    
    async def initialize(self) -> bool:
        """异步初始化服务"""
        with self.init_lock:
            if self.is_initialized:
                return True
            
            try:
                print("Initializing upgraded retrieval service...")
                
                if not self.index_file.exists():
                    print(f"ERROR: Complete index not found: {self.index_file}")
                    return False
                
                # 加载完整语义索引
                with open(self.index_file, 'rb') as f:
                    index_data = pickle.load(f)
                
                self.vectors = index_data['vectors']
                self.metadata = index_data['metadata']
                
                # 初始化embedding模型
                self.embedding_model = SemanticTextEmbedding()
                await asyncio.get_event_loop().run_in_executor(
                    None, self.embedding_model.initialize
                )
                
                self.stats.update({
                    'total_documents': len(self.metadata),
                    'vector_dimension': self.vectors.shape[1] if self.vectors is not None else 0
                })
                
                self.is_initialized = True
                
                # 新增：初始化智能混合排序服务
                try:
                    from .intelligent_hybrid_ranking import get_intelligent_hybrid_service
                    self.hybrid_ranking_service = await get_intelligent_hybrid_service()
                    print("  - Intelligent Hybrid Ranking: Enabled")
                except Exception as e:
                    print(f"  - Intelligent Hybrid Ranking: Failed ({e})")
                    self.hybrid_ranking_service = None
                
                print(f"Service upgraded successfully!")
                print(f"  - Documents: {self.stats['total_documents']} (was 150)")
                print(f"  - Model: sentence-transformers (was TF-IDF)")
                print(f"  - Vector dimension: {self.stats['vector_dimension']}")
                
                return True
                
            except Exception as e:
                print(f"Service initialization failed: {str(e)}")
                return False
    
    async def search(self, query: str, top_k: int = 10, 
                    min_similarity: float = 0.0,
                    doc_types: Optional[List[str]] = None,
                    include_metadata: bool = True,
                    enable_intelligent_ranking: bool = True,
                    enable_enhanced_scoring: bool = True) -> Dict[str, Any]:
        """执行语义检索 - 向后兼容API"""
        
        if not self.is_initialized:
            await self.initialize()
            
        if not self.is_initialized:
            return {'error': 'Service initialization failed', 'results': [], 'total': 0}
        
        search_start = time.time()
        
        try:
            # 语义向量化查询
            query_vector = await asyncio.get_event_loop().run_in_executor(
                None, self.embedding_model.encode_query, query
            )
            
            # 计算语义相似度
            similarities = np.dot(self.vectors, query_vector)
            
            # 应用过滤条件
            valid_indices = np.where(similarities >= min_similarity)[0]
            
            if doc_types:
                type_mask = np.array([
                    self.metadata[i]['type'] in doc_types 
                    for i in valid_indices
                ])
                valid_indices = valid_indices[type_mask]
            
            if len(valid_indices) == 0:
                return {
                    'query': query, 'results': [], 'total': 0,
                    'search_time': time.time() - search_start,
                    'message': 'No results found'
                }
            
            # 排序并获取top-k
            valid_similarities = similarities[valid_indices]
            sorted_indices = valid_indices[np.argsort(valid_similarities)[::-1]]
            top_indices = sorted_indices[:top_k]
            
            # 构建结果（向后兼容格式）
            results = []
            for idx in top_indices:
                metadata = self.metadata[idx]
                raw_similarity = float(similarities[idx])
                
                # 基础结果构建
                result = {
                    'id': metadata['id'],
                    'type': metadata['type'], 
                    'title': metadata['title'],
                    'score': raw_similarity,  # 将在增强评分后更新
                    'content': metadata.get('content_preview', '')[:500],
                    'similarity': raw_similarity,
                    'raw_similarity': raw_similarity  # 保留原始分数用于对比
                }
                
                if include_metadata:
                    result['metadata'] = {
                        'source': metadata.get('source', 'unknown'),
                        'version': '0.4.0_enhanced_scoring'
                    }
                
                results.append(result)
            
            # 新增：应用增强评分系统
            if enable_enhanced_scoring:
                try:
                    from .enhanced_scoring_service import get_enhanced_scoring_service
                    scoring_service = get_enhanced_scoring_service()
                    
                    # 对每个结果应用增强评分
                    for result in results:
                        enhanced_result = scoring_service.compute_enhanced_final_score(
                            query, result, result['raw_similarity']
                        )
                        
                        # 更新分数
                        result['score'] = enhanced_result['final_score']
                        result['similarity'] = enhanced_result['final_score']
                        result['scoring_details'] = enhanced_result
                    
                    # 根据新分数重新排序
                    results.sort(key=lambda x: x['score'], reverse=True)
                    
                    print(f"Enhanced scoring applied: score range {min(r['score'] for r in results):.4f}-{max(r['score'] for r in results):.4f}")
                    
                except Exception as e:
                    print(f"Warning: Enhanced scoring failed - {e}")
                    # 继续使用原始分数
            
            # 新增：应用智能混合排序增强
            if enable_intelligent_ranking and self.hybrid_ranking_service:
                try:
                    # 1. 先进行查询扩展
                    expansion_info = await self.hybrid_ranking_service.expand_user_query(query)
                    
                    # 2. 应用多信号融合排序
                    results = await self.hybrid_ranking_service.enhance_search_results(
                        query, results, expansion_info
                    )
                    
                    print(f"Intelligent ranking applied: {len(results)} results enhanced")
                    
                except Exception as e:
                    print(f"Warning: Intelligent ranking failed - {e}")
            
            # 更新搜索统计
            search_time = time.time() - search_start
            self.stats['total_searches'] += 1
            self.stats['average_search_time'] = (
                (self.stats['average_search_time'] * (self.stats['total_searches'] - 1) + search_time)
                / self.stats['total_searches']
            )
            
            return {
                'query': query,
                'results': results, 
                'total': len(results),
                'search_time': search_time,
                'message': f'Found {len(results)} results with {"enhanced+hybrid" if enable_enhanced_scoring and enable_intelligent_ranking and self.hybrid_ranking_service else "enhanced" if enable_enhanced_scoring else "semantic"} search',
                'intelligent_ranking_enabled': enable_intelligent_ranking and self.hybrid_ranking_service is not None,
                'service_version': self.stats['service_version']
            }
            
        except Exception as e:
            search_time = time.time() - search_start
            return {
                'query': query, 'results': [], 'total': 0,
                'error': str(e), 'search_time': search_time
            }
    
    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取文档详情"""
        if not self.is_initialized:
            await self.initialize()
            
        for i, metadata in enumerate(self.metadata):
            if metadata['id'] == doc_id:
                return {**metadata, 'index_position': i, 'version': '0.3.0_semantic'}
        return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            **self.stats,
            'is_initialized': self.is_initialized,
            'upgrade_info': {
                'from_version': '0.2.0_tfidf',
                'to_version': '0.3.0_semantic',
                'documents_before': 150,
                'documents_after': self.stats['total_documents']
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'status': 'healthy' if self.is_initialized else 'initializing',
            'version': '0.3.0_semantic',
            'ready': self.is_initialized,
            'total_documents': self.stats['total_documents'],
            'upgrade_complete': True,
            'timestamp': time.time()
        }

# 全局服务实例
_retrieval_service = None

async def get_retrieval_service() -> RetrievalService:
    """获取全局检索服务实例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
        await _retrieval_service.initialize()
    return _retrieval_service
