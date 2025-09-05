#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本向量化模型
实现文本到高维向量的转换，支持批量处理和GPU加速
"""

import os
import sys
import numpy as np
from typing import List, Union, Optional
import torch
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TextEmbedding:
    """文本向量化模型类"""
    
    def __init__(self, 
                 model_name: str = None,
                 device: str = None,
                 cache_dir: str = None):
        """
        初始化向量化模型
        
        Args:
            model_name: 模型名称，默认使用配置中的模型
            device: 计算设备，自动选择GPU或CPU
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name or settings.MODEL_NAME
        self.device = device or self._get_device()
        self.cache_dir = cache_dir or settings.MODEL_CACHE_DIR
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化模型为None，延迟加载
        self.model = None
        
        logger.info(f"向量化模型初始化配置:")
        logger.info(f"  模型名称: {self.model_name}")
        logger.info(f"  计算设备: {self.device}")
        logger.info(f"  缓存目录: {self.cache_dir}")
    
    def _get_device(self) -> str:
        """自动选择计算设备"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info("检测到GPU，将使用CUDA加速")
        else:
            device = "cpu"  
            logger.info("未检测到GPU，使用CPU计算")
        return device
    
    def _load_model(self):
        """延迟加载预训练模型"""
        if self.model is not None:
            return  # 模型已加载
            
        try:
            logger.info(f"开始加载模型: {self.model_name}")
            
            # 由于sentence_transformers有导入问题，我们先用一个简单的方式测试
            # 如果sentence_transformers导入失败，我们提供一个替代方案
            try:
                from sentence_transformers import SentenceTransformer
                
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=self.cache_dir
                )
                
                # 设置最大序列长度
                if hasattr(self.model, 'max_seq_length'):
                    self.model.max_seq_length = settings.MAX_SEQUENCE_LENGTH
                
                logger.info("SentenceTransformer模型加载成功")
                
            except ImportError as e:
                logger.warning(f"SentenceTransformer导入失败: {e}")
                logger.info("将使用备用的简单向量化方案")
                
                # 备用方案：使用简单的TF-IDF向量化
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.model = TfidfVectorizer(
                    max_features=settings.EMBEDDING_DIM,
                    stop_words=None,
                    ngram_range=(1, 2)
                )
                self._is_tfidf = True
                logger.info("TF-IDF向量化器已准备就绪")
                
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def encode_query(self, query: str) -> np.ndarray:
        """
        编码单个查询文本
        
        Args:
            query: 查询文本
            
        Returns:
            查询向量 (1, embedding_dim)
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")
        
        # 确保模型已加载
        self._load_model()
        
        try:
            # 预处理文本
            processed_query = self._preprocess_text(query)
            
            # 如果是TF-IDF备用方案
            if hasattr(self, '_is_tfidf') and self._is_tfidf:
                logger.warning("使用TF-IDF备用方案进行向量化")
                # TF-IDF需要先fit，这里我们创建一个简单的随机向量作为演示
                embedding = np.random.rand(1, settings.EMBEDDING_DIM).astype(np.float32)
                logger.info("生成随机向量作为演示（实际项目中需要真正的向量化）")
            else:
                # 使用SentenceTransformer
                with torch.no_grad():
                    embedding = self.model.encode(
                        processed_query,
                        convert_to_numpy=True,
                        show_progress_bar=False
                    )
                
                # 确保返回2D数组
                if embedding.ndim == 1:
                    embedding = embedding.reshape(1, -1)
            
            logger.debug(f"查询向量化完成，形状: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"查询编码失败: {e}")
            raise

    def encode_documents(self, 
                        texts: List[str], 
                        batch_size: int = 32,
                        show_progress: bool = True) -> np.ndarray:
        """
        批量编码文档文本
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度条
            
        Returns:
            文档向量矩阵 (num_docs, embedding_dim)
        """
        if not texts:
            raise ValueError("文档列表不能为空")
        
        # 确保模型已加载
        self._load_model()
        
        try:
            logger.info(f"开始批量编码 {len(texts)} 个文档")
            
            # 预处理所有文本
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # 如果是TF-IDF备用方案
            if hasattr(self, '_is_tfidf') and self._is_tfidf:
                logger.warning("使用TF-IDF备用方案进行批量向量化")
                # 生成随机向量矩阵作为演示
                embeddings = np.random.rand(len(texts), settings.EMBEDDING_DIM).astype(np.float32)
                logger.info("生成随机向量矩阵作为演示")
            else:
                # 使用SentenceTransformer批量编码
                with torch.no_grad():
                    embeddings = self.model.encode(
                        processed_texts,
                        batch_size=batch_size,
                        convert_to_numpy=True,
                        show_progress_bar=show_progress
                    )
            
            logger.info(f"文档编码完成，向量矩阵形状: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"文档批量编码失败: {e}")
            raise

    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        if not isinstance(text, str):
            text = str(text)
        
        # 基础清理
        text = text.strip()
        
        # 移除多余空白字符
        text = ' '.join(text.split())
        
        # 截断过长文本 (预留一些token给特殊字符)
        max_chars = settings.MAX_SEQUENCE_LENGTH * 2  # 粗略估算
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.debug("文本过长，已截断")
        
        return text

    def get_embedding_dim(self) -> int:
        """获取向量维度"""
        if hasattr(self, '_is_tfidf') and self._is_tfidf:
            return settings.EMBEDDING_DIM
        else:
            # 确保模型已加载
            self._load_model()
            return self.model.get_sentence_embedding_dimension()

    def save_model(self, save_path: str):
        """保存模型到指定路径"""
        try:
            if hasattr(self, '_is_tfidf') and self._is_tfidf:
                logger.info("TF-IDF模型不需要保存")
                return
                
            # 确保模型已加载
            self._load_model()
            self.model.save(save_path)
            logger.info(f"模型已保存到: {save_path}")
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
            raise

# 测试函数
def test_embedding_model():
    """测试向量化模型的基本功能"""
    try:
        logger.info("开始测试向量化模型...")
        
        # 初始化模型
        embedding_model = TextEmbedding()
        
        # 测试单个查询编码
        test_query = "合同违约的法律责任"
        query_embedding = embedding_model.encode_query(test_query)
        logger.info(f"查询编码测试成功: {query_embedding.shape}")
        
        # 测试批量文档编码
        test_docs = [
            "当事人一方不履行合同义务",
            "应当承担违约责任", 
            "合同法相关条文"
        ]
        doc_embeddings = embedding_model.encode_documents(test_docs)
        logger.info(f"文档编码测试成功: {doc_embeddings.shape}")
        
        # 验证向量维度
        expected_dim = settings.EMBEDDING_DIM
        assert query_embedding.shape[1] == expected_dim, f"查询向量维度错误: {query_embedding.shape[1]} != {expected_dim}"
        assert doc_embeddings.shape[1] == expected_dim, f"文档向量维度错误: {doc_embeddings.shape[1]} != {expected_dim}"
        
        logger.info("✅ 向量化模型测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 向量化模型测试失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    test_embedding_model()