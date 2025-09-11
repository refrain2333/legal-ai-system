#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载管理器
统一管理向量数据、原始数据、模型加载等
"""

import pickle
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """统一数据加载管理器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化数据加载器
        
        Args:
            project_root: 项目根目录，如果不提供则自动推断
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = Path(project_root)
        self.vectors_dir = self.project_root / "data/processed/vectors"
        self.criminal_dir = self.project_root / "data/processed/criminal"
        
        # 数据存储
        self.vectors_data = {}
        self.original_data = {}
        self.model = None
        
        # 缓存控制
        self.content_cache = {}
        self.cache_size_limit = 1000  # 最多缓存1000个完整内容
        
        # 线程安全
        self._lock = Lock()
        
        # 加载状态
        self.vectors_loaded = False
        self.original_loaded = False
        self.model_loaded = False
        
        logger.info(f"DataLoader initialized with project root: {self.project_root}")
    
    def load_all(self) -> Dict[str, Any]:
        """
        加载所有数据（向量+原始数据+模型）
        
        Returns:
            加载状态和统计信息
        """
        start_time = time.time()
        
        # 并行加载（按需优化为真正的并行）
        vector_stats = self.load_vectors()
        original_stats = self.load_original_data()
        model_stats = self.load_model()
        
        total_time = time.time() - start_time
        
        stats = {
            'success': True,
            'total_loading_time': total_time,
            'vectors': vector_stats,
            'original_data': original_stats,
            'model': model_stats,
            'total_documents': self.get_total_document_count(),
            'memory_usage_mb': self._estimate_memory_usage()
        }
        
        logger.info(f"All data loaded successfully in {total_time:.2f}s")
        return stats
    
    def load_vectors(self) -> Dict[str, Any]:
        """加载向量数据"""
        if self.vectors_loaded:
            return {'status': 'already_loaded'}
        
        start_time = time.time()
        stats = {'articles': 0, 'cases': 0, 'errors': []}
        
        try:
            # 加载法条向量
            articles_file = self.vectors_dir / "criminal_articles_vectors.pkl"
            if articles_file.exists():
                with open(articles_file, 'rb') as f:
                    self.vectors_data['articles'] = pickle.load(f)
                    stats['articles'] = self.vectors_data['articles']['total_count']
                    logger.info(f"Loaded {stats['articles']} article vectors")
            else:
                stats['errors'].append("criminal_articles_vectors.pkl not found")
            
            # 加载案例向量
            cases_file = self.vectors_dir / "criminal_cases_vectors.pkl"
            if cases_file.exists():
                with open(cases_file, 'rb') as f:
                    self.vectors_data['cases'] = pickle.load(f)
                    stats['cases'] = self.vectors_data['cases']['total_count']
                    logger.info(f"Loaded {stats['cases']} case vectors")
            else:
                stats['errors'].append("criminal_cases_vectors.pkl not found")
            
            self.vectors_loaded = len(stats['errors']) == 0
            loading_time = time.time() - start_time
            
            stats.update({
                'status': 'success' if self.vectors_loaded else 'partial',
                'loading_time': loading_time,
                'total_vectors': stats['articles'] + stats['cases']
            })
            
        except Exception as e:
            stats.update({
                'status': 'error',
                'error': str(e),
                'loading_time': time.time() - start_time
            })
            logger.error(f"Error loading vectors: {e}")
        
        return stats
    
    def load_original_data(self) -> Dict[str, Any]:
        """加载原始数据（延迟加载，需要时才加载）"""
        if self.original_loaded:
            return {'status': 'already_loaded'}
        
        start_time = time.time()
        stats = {'articles': 0, 'cases': 0, 'errors': []}
        
        try:
            # 检查文件存在性（不立即加载，节省内存）
            articles_file = self.criminal_dir / "criminal_articles.pkl"
            cases_file = self.criminal_dir / "criminal_cases.pkl"
            
            if not articles_file.exists():
                stats['errors'].append("criminal_articles.pkl not found")
            if not cases_file.exists():
                stats['errors'].append("criminal_cases.pkl not found")
            
            # 标记为已"检查"，实际数据在需要时加载
            self.original_loaded = len(stats['errors']) == 0
            loading_time = time.time() - start_time
            
            stats.update({
                'status': 'checked' if self.original_loaded else 'error',
                'loading_time': loading_time,
                'note': 'Original data files checked but not loaded (lazy loading)'
            })
            
        except Exception as e:
            stats.update({
                'status': 'error',
                'error': str(e),
                'loading_time': time.time() - start_time
            })
            logger.error(f"Error checking original data: {e}")
        
        return stats
    
    def load_model(self) -> Dict[str, Any]:
        """加载语义模型"""
        if self.model_loaded:
            return {'status': 'already_loaded', 'model_name': 'shibing624/text2vec-base-chinese'}
        
        start_time = time.time()
        
        try:
            logger.info("Loading semantic model...")
            self.model = SentenceTransformer('shibing624/text2vec-base-chinese')
            self.model_loaded = True
            
            loading_time = time.time() - start_time
            
            stats = {
                'status': 'success',
                'model_name': 'shibing624/text2vec-base-chinese',
                'embedding_dim': 768,
                'loading_time': loading_time
            }
            
            logger.info(f"Model loaded successfully in {loading_time:.2f}s")
            
        except Exception as e:
            stats = {
                'status': 'error',
                'error': str(e),
                'loading_time': time.time() - start_time
            }
            logger.error(f"Error loading model: {e}")
        
        return stats
    
    def get_article_content(self, article_id: str) -> Optional[str]:
        """获取法条完整内容"""
        return self._get_content_from_original('articles', article_id, 'content')
    
    def get_case_content(self, case_id: str) -> Optional[str]:
        """获取案例完整内容"""
        return self._get_content_from_original('cases', case_id, 'fact')
    
    def _get_content_from_original(self, data_type: str, item_id: str, content_field: str) -> Optional[str]:
        """从原始数据获取完整内容（带缓存）"""
        cache_key = f"{data_type}_{item_id}"
        
        # 检查缓存
        if cache_key in self.content_cache:
            return self.content_cache[cache_key]
        
        with self._lock:
            # 双重检查
            if cache_key in self.content_cache:
                return self.content_cache[cache_key]
            
            # 加载原始数据
            if data_type not in self.original_data:
                self._load_original_data_type(data_type)
            
            # 查找内容
            content = None
            if data_type in self.original_data:
                for item in self.original_data[data_type]:
                    # 处理不同的ID格式和前缀重复问题
                    item_actual_id = None
                    if hasattr(item, 'case_id'):
                        item_actual_id = item.case_id
                    elif hasattr(item, 'document_id'):
                        item_actual_id = item.document_id
                    elif isinstance(item, dict):
                        item_actual_id = item.get('case_id') or item.get('id')
                    
                    # 扩展ID匹配逻辑，处理重复前缀问题
                    if item_actual_id and self._ids_match(item_actual_id, item_id):
                        if hasattr(item, content_field):
                            content = getattr(item, content_field)
                        elif isinstance(item, dict):
                            content = item.get(content_field)
                        break
            
            # 缓存管理
            if content:
                if len(self.content_cache) >= self.cache_size_limit:
                    # 简单的LRU：删除一些旧缓存
                    keys_to_remove = list(self.content_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.content_cache[key]
                
                self.content_cache[cache_key] = content
            
            return content
    
    def _ids_match(self, actual_id: str, search_id: str) -> bool:
        """
        检查两个ID是否匹配，处理各种前缀情况
        
        Args:
            actual_id: 实际数据中的ID (如 "case_000001")
            search_id: 搜索的ID (如 "case_case_000001")
        """
        if actual_id == search_id:
            return True
        
        # 处理重复前缀问题：case_case_000001 应该匹配 case_000001
        if search_id.startswith('case_case_') and actual_id.startswith('case_'):
            return actual_id == search_id.replace('case_case_', 'case_')
        
        # 处理缺少前缀问题：case_000001 应该匹配 000001
        if actual_id.startswith('case_') and not search_id.startswith('case_'):
            return actual_id == f'case_{search_id}'
        
        # 处理去除前缀：000001 应该匹配 case_000001
        if search_id.startswith('case_') and not actual_id.startswith('case_'):
            return search_id == f'case_{actual_id}'
        
        return False
    
    def _load_original_data_type(self, data_type: str):
        """加载特定类型的原始数据"""
        try:
            # 导入兼容性模块以支持旧的pickle文件
            try:
                from . import legacy_compatibility
            except ImportError:
                pass  # 如果兼容性模块不存在，继续尝试加载
            
            if data_type == 'articles':
                file_path = self.criminal_dir / "criminal_articles.pkl"
            elif data_type == 'cases':
                file_path = self.criminal_dir / "criminal_cases.pkl"
            else:
                return
            
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    self.original_data[data_type] = pickle.load(f)
                    logger.info(f"Loaded {len(self.original_data[data_type])} {data_type} from original data")
            
        except Exception as e:
            logger.error(f"Error loading original {data_type}: {e}")
    
    def get_vectors(self, data_type: str) -> Optional[np.ndarray]:
        """获取向量数据"""
        if not self.vectors_loaded or data_type not in self.vectors_data:
            return None
        return self.vectors_data[data_type]['vectors']
    
    def get_metadata(self, data_type: str) -> Optional[List[Dict]]:
        """获取元数据"""
        if not self.vectors_loaded or data_type not in self.vectors_data:
            return None
        return self.vectors_data[data_type]['metadata']
    
    def encode_query(self, query: str) -> Optional[np.ndarray]:
        """编码查询文本"""
        if not self.model_loaded:
            model_stats = self.load_model()
            if model_stats['status'] != 'success':
                return None
        
        try:
            return self.model.encode([query])
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            return None
    
    def get_total_document_count(self) -> int:
        """获取总文档数量"""
        total = 0
        if self.vectors_loaded:
            for data_type in self.vectors_data:
                total += self.vectors_data[data_type]['total_count']
        return total
    
    def _estimate_memory_usage(self) -> float:
        """估算内存使用量（MB）"""
        total_mb = 0
        
        # 向量数据
        if self.vectors_loaded:
            for data_type in self.vectors_data:
                vectors = self.vectors_data[data_type]['vectors']
                total_mb += vectors.nbytes / (1024 * 1024)
        
        # 模型（估算）
        if self.model_loaded:
            total_mb += 500  # text2vec-base-chinese大约500MB
        
        # 缓存内容
        total_mb += len(self.content_cache) * 0.01  # 每个缓存项大约10KB
        
        return total_mb
    
    def get_stats(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        return {
            'vectors_loaded': self.vectors_loaded,
            'original_data_checked': self.original_loaded,
            'model_loaded': self.model_loaded,
            'total_documents': self.get_total_document_count(),
            'cached_contents': len(self.content_cache),
            'memory_usage_mb': self._estimate_memory_usage(),
            'data_types': list(self.vectors_data.keys()) if self.vectors_loaded else []
        }
    
    def clear_cache(self):
        """清空内容缓存"""
        with self._lock:
            self.content_cache.clear()
            logger.info("Content cache cleared")
    
    def reload_vectors(self) -> Dict[str, Any]:
        """重新加载向量数据"""
        self.vectors_data.clear()
        self.vectors_loaded = False
        return self.load_vectors()


# 全局单例
_data_loader = None
_loader_lock = Lock()

def get_data_loader() -> DataLoader:
    """获取全局数据加载器实例"""
    global _data_loader
    if _data_loader is None:
        with _loader_lock:
            if _data_loader is None:
                _data_loader = DataLoader()
    return _data_loader

# 便捷函数
def load_all_data() -> Dict[str, Any]:
    """加载所有数据的便捷函数"""
    return get_data_loader().load_all()

def get_article_content(article_id: str) -> Optional[str]:
    """获取法条内容的便捷函数"""
    return get_data_loader().get_article_content(article_id)

def get_case_content(case_id: str) -> Optional[str]:
    """获取案例内容的便捷函数"""
    return get_data_loader().get_case_content(case_id)

def encode_query(query: str) -> Optional[np.ndarray]:
    """编码查询的便捷函数"""
    return get_data_loader().encode_query(query)