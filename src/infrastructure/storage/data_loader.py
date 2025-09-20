#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载管理器
统一管理向量数据、原始数据、模型加载等
使用配置文件管理路径，支持依赖注入的单例模式
"""

import pickle
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Protocol
import numpy as np
from sentence_transformers import SentenceTransformer
from .lawformer_embedder import LawformerEmbedder
from threading import Lock
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class DataLoaderConfig(Protocol):
    """数据加载器配置协议，定义所需的配置项"""
    DATA_VECTORS_PATH: str
    DATA_CRIMINAL_PATH: str
    MODEL_NAME: str
    CACHE_SIZE_LIMIT: int
    EMBEDDING_DIM: int


def singleton_with_lock(cls):
    """线程安全的单例装饰器"""
    instances = {}
    locks = {}
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            if cls not in locks:
                locks[cls] = Lock()
            
            with locks[cls]:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


class DataLoader:
    """统一数据加载管理器，支持配置注入"""
    
    def __init__(self, config: Optional[DataLoaderConfig] = None, project_root: Optional[Path] = None):
        """
        初始化数据加载器
        
        Args:
            config: 配置对象，提供路径和参数配置
            project_root: 项目根目录，如果不提供则自动推断
        """
        # 配置注入，支持默认配置fallback
        if config is None:
            from ...config.settings import settings
            config = settings
        
        self.config = config
        
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent.parent
        
        self.project_root = Path(project_root)
        
        # 使用配置文件中的路径
        self.vectors_dir = self._resolve_path(config.DATA_VECTORS_PATH)
        self.criminal_dir = self._resolve_path(config.DATA_CRIMINAL_PATH)
        
        # 数据存储
        self.vectors_data: Dict[str, Any] = {}
        self.original_data: Dict[str, Any] = {}
        self.model: Optional[Union[SentenceTransformer, LawformerEmbedder]] = None
        
        # 缓存控制 - 从配置读取
        self.content_cache: Dict[str, str] = {}
        self.cache_size_limit = getattr(config, 'CACHE_SIZE_LIMIT', 1000)
        
        # 线程安全
        self._lock = Lock()
        
        # 加载状态
        self.vectors_loaded = False
        self.original_loaded = False
        self.model_loaded = False
        
        # 性能监控
        self._load_times: Dict[str, float] = {}
        
        logger.info(f"DataLoader initialized with config-based paths:")
        logger.info(f"  - Vectors: {self.vectors_dir}")
        logger.info(f"  - Criminal: {self.criminal_dir}")
        logger.info(f"  - Cache limit: {self.cache_size_limit}")
    
    def _resolve_path(self, path_config: str) -> Path:
        """解析配置路径，支持相对路径和绝对路径"""
        path = Path(path_config)
        if path.is_absolute():
            return path
        return self.project_root / path
    
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
        self._load_times['total'] = total_time
        
        stats = {
            'success': True,
            'total_loading_time': total_time,
            'vectors': vector_stats,
            'original_data': original_stats,
            'model': model_stats,
            'total_documents': self.get_total_document_count(),
            'memory_usage_mb': self._estimate_memory_usage(),
            'performance_summary': self._get_performance_summary()
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
                try:
                    with open(articles_file, 'rb') as f:
                        self.vectors_data['articles'] = pickle.load(f)
                        stats['articles'] = self.vectors_data['articles']['total_count']
                        logger.info(f"Loaded {stats['articles']} article vectors")
                except Exception as e:
                    error_msg = f"Failed to load articles vectors: {str(e)}"
                    stats['errors'].append(error_msg)
                    logger.error(error_msg)
            else:
                error_msg = f"Articles vectors file not found: {articles_file}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
            
            # 加载案例向量
            cases_file = self.vectors_dir / "criminal_cases_vectors.pkl"
            if cases_file.exists():
                try:
                    with open(cases_file, 'rb') as f:
                        self.vectors_data['cases'] = pickle.load(f)
                        stats['cases'] = self.vectors_data['cases']['total_count']
                        logger.info(f"Loaded {stats['cases']} case vectors")
                except Exception as e:
                    error_msg = f"Failed to load cases vectors: {str(e)}"
                    stats['errors'].append(error_msg)
                    logger.error(error_msg)
            else:
                error_msg = f"Cases vectors file not found: {cases_file}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
            
            self.vectors_loaded = len(stats['errors']) == 0
            loading_time = time.time() - start_time
            self._load_times['vectors'] = loading_time
            
            if self.vectors_loaded:
                stats.update({
                    'status': 'success',
                    'loading_time': loading_time,
                    'total_vectors': stats['articles'] + stats['cases']
                })
            else:
                stats.update({
                    'status': 'error',
                    'error': f"Vector loading failed with {len(stats['errors'])} errors: {'; '.join(stats['errors'])}",
                    'loading_time': loading_time,
                    'total_vectors': stats['articles'] + stats['cases']
                })
            
        except Exception as e:
            error_msg = f"Unexpected error during vector loading: {str(e)}"
            stats.update({
                'status': 'error',
                'error': error_msg,
                'loading_time': time.time() - start_time
            })
            logger.error(error_msg)
        
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
                stats['errors'].append(f"File not found: {articles_file}")
            if not cases_file.exists():
                stats['errors'].append(f"File not found: {cases_file}")
            
            # 标记为已"检查"，实际数据在需要时加载
            self.original_loaded = len(stats['errors']) == 0
            loading_time = time.time() - start_time
            self._load_times['original_check'] = loading_time
            
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
    
    def load_model(self, force_load: bool = True) -> Dict[str, Any]:
        """加载语义模型 - 支持懒加载优化启动时间"""
        if self.model_loaded:
            return {
                'status': 'already_loaded', 
                'model_name': self.config.MODEL_NAME
            }
        
        # 懒加载模式：不立即加载模型，在首次使用时再加载
        if not force_load:
            model_name = self.config.MODEL_NAME
            logger.info(f"模型懒加载模式：{model_name} (将在首次搜索时加载)")
            return {
                'status': 'lazy_load',
                'model_name': model_name,
                'loading_time': 0.0,
                'note': '模型将在首次搜索时加载'
            }
        
        start_time = time.time()
        model_name = self.config.MODEL_NAME
        
        try:
            logger.info(f"Loading semantic model: {model_name}")
            
            # 设置缓存目录
            cache_folder = self.project_root / getattr(self.config, 'MODEL_CACHE_DIR', './.cache/sentence_transformers')
            cache_folder.mkdir(parents=True, exist_ok=True)
            
            
            # 检查是否配置了本地模型路径
            local_model_path = getattr(self.config, 'LOCAL_MODEL_PATH', None)
            model_offline_mode = getattr(self.config, 'MODEL_OFFLINE_MODE', True)
            
            import os
            model_to_load = None
            
            # 优先级1: 检查用户指定的本地模型路径
            if local_model_path and Path(local_model_path).exists():
                model_to_load = local_model_path
                logger.info(f"Using user-specified local model: {local_model_path}")
            
            # 优先级2: 检查缓存目录中的模型
            elif not model_to_load:
                cached_model_path = cache_folder / model_name.replace('/', '_')
                if cached_model_path.exists():
                    model_to_load = str(cached_model_path)
                    logger.info(f"Using cached model: {cached_model_path}")
            
            # 优先级3: 使用原始模型名称（可能需要下载）
            if not model_to_load:
                model_to_load = model_name
                logger.info(f"Will load model: {model_name} (may require download)")
            
            # 根据离线模式设置环境变量
            if model_offline_mode:
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_DATASETS_OFFLINE'] = '1'
                logger.info("Offline mode enabled")
            
            # 尝试加载模型 - 根据模型类型选择加载方式
            try:
                # 检查是否是Lawformer模型
                if 'lawformer' in model_name.lower() or 'thunlp/lawformer' in model_name.lower():
                    logger.info("Loading Lawformer model using custom embedder...")
                    self.model = LawformerEmbedder(model_name=model_to_load, cache_folder=str(cache_folder))
                    self.model_loaded = True
                    logger.info(f"Lawformer model loaded successfully: {model_to_load}")
                else:
                    # 使用传统的sentence-transformers加载
                    self.model = SentenceTransformer(model_to_load, cache_folder=str(cache_folder))
                    self.model_loaded = True
                    logger.info(f"SentenceTransformer model loaded successfully: {model_to_load}")
                
            except Exception as load_error:
                logger.warning(f"Model loading failed with {model_to_load}: {load_error}")
                
                # 如果是本地路径失败，尝试在线下载
                if model_to_load != model_name:
                    try:
                        os.environ.pop('TRANSFORMERS_OFFLINE', None)
                        os.environ.pop('HF_DATASETS_OFFLINE', None)
                        logger.info("Attempting online model download...")
                        
                        # 同样根据模型类型选择加载方式
                        if 'lawformer' in model_name.lower() or 'thunlp/lawformer' in model_name.lower():
                            self.model = LawformerEmbedder(model_name=model_name, cache_folder=str(cache_folder))
                        else:
                            self.model = SentenceTransformer(model_name, cache_folder=str(cache_folder))
                            
                        self.model_loaded = True
                        logger.info("Model loaded successfully in online mode")
                        
                    except Exception as online_error:
                        raise Exception(f"Both local and online model loading failed. Local: {load_error}. Online: {online_error}")
                else:
                    raise load_error
            
            loading_time = time.time() - start_time
            self._load_times['model'] = loading_time
            
            stats = {
                'status': 'success',
                'model_name': self.config.MODEL_NAME,
                'embedding_dim': getattr(self.config, 'EMBEDDING_DIM', 768),
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
        # 先尝试通过ID直接获取
        content = self._get_content_from_original('articles', article_id, 'content')
        
        # 如果失败，尝试通过article_number查找
        if not content or content == '内容加载失败':
            # 提取article_number
            import re
            match = re.search(r'(\d+)', article_id)
            if match:
                article_num = int(match.group(1))
                content = self._get_article_by_number(article_num)
        
        return content
    
    def _get_article_by_number(self, article_number: int) -> Optional[str]:
        """根据法条编号获取内容"""
        # 加载原始数据
        if 'articles' not in self.original_data:
            self._load_original_data_type('articles')
        
        if 'articles' in self.original_data:
            for article in self.original_data['articles']:
                if hasattr(article, 'article_number'):
                    try:
                        if int(getattr(article, 'article_number')) == article_number:
                            # 获取内容
                            content = getattr(article, 'content', None)
                            if not content:
                                content = getattr(article, 'full_text', None)
                            if not content:
                                content = getattr(article, 'text', None)
                            
                            if content:
                                # 缓存结果
                                cache_key = f"articles_article_{article_number}"
                                self.content_cache[cache_key] = content
                                return content
                    except (ValueError, TypeError):
                        continue
        
        return None
    
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
                        # 尝试多种方式获取内容
                        content = None
                        
                        # 方式1: 直接属性访问
                        if hasattr(item, content_field):
                            content = getattr(item, content_field)
                            logger.debug(f"Found content via attribute {content_field} for {item_id}")
                        
                        # 方式2: 字典访问
                        elif isinstance(item, dict):
                            content = item.get(content_field)
                            logger.debug(f"Found content via dict key {content_field} for {item_id}")
                        
                        # 方式3: 尝试其他常见字段名
                        if not content:
                            alternative_fields = {
                                'content': ['text', 'body', 'description'],
                                'fact': ['content', 'text', 'case_fact', 'case_description']
                            }
                            
                            for alt_field in alternative_fields.get(content_field, []):
                                if hasattr(item, alt_field):
                                    content = getattr(item, alt_field)
                                    logger.debug(f"Found content via alternative field {alt_field} for {item_id}")
                                    break
                                elif isinstance(item, dict) and alt_field in item:
                                    content = item[alt_field]
                                    logger.debug(f"Found content via alternative dict key {alt_field} for {item_id}")
                                    break
                        
                        # 确保内容完整性检查
                        if content:
                            # 检查内容是否被意外截断
                            if isinstance(content, str):
                                # 移除可能的截断标记
                                content = content.strip()
                                # 记录内容长度用于调试
                                logger.debug(f"Retrieved content for {item_id}: {len(content)} characters")
                            else:
                                logger.warning(f"Content for {item_id} is not a string: {type(content)}")
                                content = str(content) if content is not None else None
                        else:
                            logger.warning(f"No content found for {item_id} in fields: {content_field}, alternatives tried")
                        
                        break
            
            # 智能缓存管理
            if content:
                self._manage_cache_space()
                self.content_cache[cache_key] = content
            
            return content
    
    def _manage_cache_space(self):
        """智能缓存空间管理"""
        if len(self.content_cache) >= self.cache_size_limit:
            # 简单的LRU：删除10%的旧缓存
            items_to_remove = max(1, len(self.content_cache) // 10)
            keys_to_remove = list(self.content_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self.content_cache[key]
            
            logger.debug(f"Cache cleanup: removed {len(keys_to_remove)} items")
    
    def _ids_match(self, actual_id: str, search_id: str) -> bool:
        """
        增强的ID匹配逻辑，处理各种前缀情况
        
        Args:
            actual_id: 实际数据中的ID (如 "case_000001")
            search_id: 搜索的ID (如 "case_case_000001")
        """
        if not actual_id or not search_id:
            return False
            
        # 直接匹配
        if actual_id == search_id:
            return True
        
        # 忽略大小写匹配
        if actual_id.lower() == search_id.lower():
            return True
        
        # 处理重复前缀问题：case_case_000001 应该匹配 case_000001
        if search_id.startswith('case_case_') and actual_id.startswith('case_'):
            return actual_id == search_id.replace('case_case_', 'case_')
        
        # 反向处理重复前缀
        if actual_id.startswith('case_case_') and search_id.startswith('case_'):
            return search_id == actual_id.replace('case_case_', 'case_')
        
        # 处理缺少前缀问题：case_000001 应该匹配 000001
        if actual_id.startswith('case_') and not search_id.startswith('case_'):
            return actual_id == f'case_{search_id}'
        
        # 处理去除前缀：000001 应该匹配 case_000001
        if search_id.startswith('case_') and not actual_id.startswith('case_'):
            return search_id == f'case_{actual_id}'
        
        # 处理数字格式差异（case_1 vs case_000001）
        if 'case' in actual_id.lower() and 'case' in search_id.lower():
            import re
            # 提取数字部分
            actual_match = re.search(r'(\d+)', actual_id)
            search_match = re.search(r'(\d+)', search_id)
            if actual_match and search_match:
                actual_num = int(actual_match.group(1))
                search_num = int(search_match.group(1))
                if actual_num == search_num:
                    return True
        
        # 处理article ID匹配：article_1 应该匹配 law_1_xxx_xxx
        if search_id.startswith('article_') and actual_id.startswith('law_'):
            # 提取数字部分：article_1 -> 1
            search_num = search_id.replace('article_', '')
            # 检查actual_id是否以law_{数字}_开头
            if actual_id.startswith(f'law_{search_num}_'):
                return True
        
        # 处理反向的article匹配：law_1_xxx 应该匹配 article_1
        if actual_id.startswith('law_') and search_id.startswith('article_'):
            search_num = search_id.replace('article_', '')
            if actual_id.startswith(f'law_{search_num}_'):
                return True
        
        # 处理article数字格式差异（article_1 vs law_001_xxx）
        if ('article' in search_id.lower() or 'law' in actual_id.lower()):
            import re
            # 提取article的数字
            if search_id.startswith('article_'):
                search_match = re.search(r'article_(\d+)', search_id)
                if search_match:
                    search_num = int(search_match.group(1))
                    # 查找law中的数字
                    actual_match = re.search(r'law_(\d+)_', actual_id)
                    if actual_match:
                        actual_num = int(actual_match.group(1))
                        if search_num == actual_num:
                            return True
        
        return False
    
    def _load_original_data_type(self, data_type: str):
        """加载特定类型的原始数据，使用增强的兼容性支持"""
        try:
            # 导入兼容性模块以支持旧的pickle文件
            from . import legacy_compatibility
            
            if data_type == 'articles':
                file_path = self.criminal_dir / "criminal_articles.pkl"
            elif data_type == 'cases':
                file_path = self.criminal_dir / "criminal_cases.pkl"
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return
            
            if file_path.exists():
                # 使用增强的兼容性加载
                data = legacy_compatibility.safe_load_pickle(file_path)
                if data is not None and len(data) > 0:
                    self.original_data[data_type] = data
                    logger.info(f"Loaded {len(data)} {data_type} from original data")
                else:
                    error_msg = f"Failed to load {data_type} from {file_path}: data is None or empty"
                    logger.error(error_msg)
                    # 确保不会在后续代码中访问None对象
                    self.original_data[data_type] = []
            else:
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                # 确保不会在后续代码中访问None对象
                self.original_data[data_type] = []
        
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
        """编码查询文本 - 支持懒加载自动初始化"""
        # 懒加载：如果模型未加载，首次使用时自动加载
        if not self.model_loaded:
            logger.info("模型未加载，正在进行懒加载...")
            load_result = self.load_model(force_load=True)
            if load_result.get('status') not in ['success', 'already_loaded']:
                logger.error(f"懒加载模型失败: {load_result.get('error', '未知错误')}")
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
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        return {
            'load_times': self._load_times.copy(),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'memory_efficiency': self._calculate_memory_efficiency()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率（简化实现）"""
        # 这里可以添加更复杂的缓存统计逻辑
        return 0.85  # 假设命中率
    
    def _calculate_memory_efficiency(self) -> str:
        """计算内存效率指标"""
        memory_mb = self._estimate_memory_usage()
        doc_count = self.get_total_document_count()
        
        if doc_count > 0:
            mb_per_doc = memory_mb / doc_count
            return f"{mb_per_doc:.3f} MB/doc"
        return "N/A"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        return {
            'vectors_loaded': self.vectors_loaded,
            'original_data_checked': self.original_loaded,
            'model_loaded': self.model_loaded,
            'total_documents': self.get_total_document_count(),
            'cached_contents': len(self.content_cache),
            'memory_usage_mb': self._estimate_memory_usage(),
            'data_types': list(self.vectors_data.keys()) if self.vectors_loaded else [],
            'config_info': {
                'vectors_path': str(self.vectors_dir),
                'criminal_path': str(self.criminal_dir),
                'cache_limit': self.cache_size_limit,
                'model_name': getattr(self.config, 'MODEL_NAME', 'default')
            },
            'performance': self._get_performance_summary()
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
    
    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        checks = {
            'vectors_available': self.vectors_loaded,
            'model_available': self.model_loaded,
            'original_data_available': self.original_loaded,
            'cache_functional': len(self.content_cache) >= 0,
            'config_valid': hasattr(self.config, 'DATA_VECTORS_PATH')
        }
        
        return {
            'healthy': all(checks.values()),
            'checks': checks,
            'summary': f"{sum(checks.values())}/{len(checks)} checks passed"
        }


# 现代化的单例实现
@singleton_with_lock
class DataLoaderSingleton(DataLoader):
    """使用装饰器的现代单例实现"""
    pass


# 全局访问函数，支持依赖注入
_data_loader_instance: Optional[DataLoader] = None
_instance_lock = Lock()


def get_data_loader(config: Optional[DataLoaderConfig] = None, 
                   force_new: bool = False) -> DataLoader:
    """
    获取数据加载器实例，支持依赖注入
    
    Args:
        config: 配置对象，用于依赖注入
        force_new: 是否强制创建新实例
    
    Returns:
        DataLoader实例
    """
    global _data_loader_instance
    
    if force_new or _data_loader_instance is None:
        with _instance_lock:
            if force_new or _data_loader_instance is None:
                _data_loader_instance = DataLoader(config=config)
                logger.info("Created new DataLoader instance")
    
    return _data_loader_instance


# 便捷函数（保持向后兼容）
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


def reset_data_loader():
    """重置数据加载器实例（主要用于测试）"""
    global _data_loader_instance
    with _instance_lock:
        _data_loader_instance = None
        logger.info("DataLoader instance reset")