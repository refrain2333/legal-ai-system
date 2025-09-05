#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版文本向量化模型
使用TF-IDF和简单的文本处理实现基本的向量化功能
适用于低配置环境和快速原型开发
"""

import os
import sys
import numpy as np
import pickle
from typing import List, Union, Optional
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SimpleTextEmbedding:
    """简化版文本向量化模型类"""
    
    def __init__(self, 
                 cache_dir: str = None,
                 max_features: int = None):
        """
        初始化向量化模型
        
        Args:
            cache_dir: 模型缓存目录
            max_features: TF-IDF最大特征数
        """
        self.cache_dir = cache_dir or settings.MODEL_CACHE_DIR
        self.max_features = max_features or settings.EMBEDDING_DIM
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化TF-IDF向量化器
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words=None,  # 中文没有预定义停用词
            ngram_range=(1, 2),  # 使用1-gram和2-gram
            min_df=1,  # 最小文档频率
            max_df=0.95,  # 最大文档频率
            sublinear_tf=True,  # 使用sublinear TF scaling
            norm='l2'  # L2归一化
        )
        
        # 是否已训练标志
        self._is_fitted = False
        self._document_vectors = None
        
        logger.info(f"简化向量化模型初始化配置:")
        logger.info(f"  最大特征数: {self.max_features}")
        logger.info(f"  缓存目录: {self.cache_dir}")
    
    def _preprocess_text(self, text: str) -> str:
        """
        中文文本预处理
        
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
        
        # 使用jieba进行中文分词
        try:
            # 使用精确模式分词
            words = jieba.cut(text, cut_all=False)
            # 过滤单字符和标点符号
            words = [word for word in words if len(word.strip()) > 1 and word.strip().isalnum()]
            text = ' '.join(words)
        except Exception as e:
            logger.warning(f"分词失败，使用原文: {e}")
        
        # 截断过长文本
        max_chars = self.max_features * 2
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.debug("文本过长，已截断")
        
        return text

    def fit(self, texts: List[str]):
        """
        在文档集合上训练TF-IDF向量化器
        
        Args:
            texts: 文档文本列表
        """
        logger.info(f"开始在 {len(texts)} 个文档上训练TF-IDF向量化器...")
        
        # 预处理所有文本
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # 训练TF-IDF向量化器
        self.vectorizer.fit(processed_texts)
        self._is_fitted = True
        
        # 计算所有文档的向量表示
        self._document_vectors = self.vectorizer.transform(processed_texts)
        
        logger.info(f"TF-IDF训练完成，词汇表大小: {len(self.vectorizer.vocabulary_)}")

    def encode_query(self, query: str) -> np.ndarray:
        """
        编码单个查询文本
        
        Args:
            query: 查询文本
            
        Returns:
            查询向量 (1, max_features)
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")
        
        if not self._is_fitted:
            raise ValueError("模型尚未训练，请先调用fit()方法")
        
        try:
            # 预处理查询文本
            processed_query = self._preprocess_text(query)
            
            # 向量化
            query_vector = self.vectorizer.transform([processed_query])
            
            # 转换为dense数组
            query_dense = query_vector.toarray().astype(np.float32)
            
            logger.debug(f"查询向量化完成，形状: {query_dense.shape}")
            return query_dense
            
        except Exception as e:
            logger.error(f"查询编码失败: {e}")
            raise

    def encode_documents(self, texts: List[str]) -> np.ndarray:
        """
        批量编码文档文本
        
        Args:
            texts: 文本列表
            
        Returns:
            文档向量矩阵 (num_docs, max_features)
        """
        if not texts:
            raise ValueError("文档列表不能为空")
        
        if not self._is_fitted:
            raise ValueError("模型尚未训练，请先调用fit()方法")
        
        try:
            logger.info(f"开始批量编码 {len(texts)} 个文档")
            
            # 预处理所有文本
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # 向量化
            doc_vectors = self.vectorizer.transform(processed_texts)
            
            # 转换为dense数组
            doc_dense = doc_vectors.toarray().astype(np.float32)
            
            logger.info(f"文档编码完成，向量矩阵形状: {doc_dense.shape}")
            return doc_dense
            
        except Exception as e:
            logger.error(f"文档批量编码失败: {e}")
            raise

    def get_embedding_dim(self) -> int:
        """获取向量维度"""
        if self._is_fitted:
            return len(self.vectorizer.vocabulary_)
        else:
            return self.max_features

    def save_model(self, save_path: str):
        """保存模型到指定路径"""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'is_fitted': self._is_fitted,
                'max_features': self.max_features
            }
            
            with open(save_path, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"模型已保存到: {save_path}")
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
            raise

    def load_model(self, load_path: str):
        """从指定路径加载模型"""
        try:
            with open(load_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.vectorizer = model_data['vectorizer']
            self._is_fitted = model_data['is_fitted']
            self.max_features = model_data.get('max_features', self.max_features)
            
            logger.info(f"模型已从 {load_path} 加载")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def compute_similarity(self, query_vector: np.ndarray, doc_vectors: np.ndarray) -> np.ndarray:
        """
        计算查询向量与文档向量的相似度
        
        Args:
            query_vector: 查询向量 (1, dim)
            doc_vectors: 文档向量矩阵 (num_docs, dim)
            
        Returns:
            相似度分数数组 (num_docs,)
        """
        try:
            # 使用余弦相似度
            similarities = cosine_similarity(query_vector, doc_vectors)[0]
            return similarities
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            raise

# 测试函数
def test_simple_embedding_model():
    """测试简化版向量化模型的基本功能"""
    try:
        logger.info("开始测试简化向量化模型...")
        
        # 准备测试数据
        test_docs = [
            "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
            "公司是企业法人，有独立的法人财产，享有法人财产权。公司以其全部财产对公司的债务承担责任。",
            "故意伤害他人身体的，处三年以下有期徒刑、拘役或者管制。致人重伤的，处三年以上十年以下有期徒刑。",
            "合同当事人应当按照约定全面履行自己的义务。当事人应当遵循诚实信用原则，根据合同的性质、目的和交易习惯履行通知、协助、保密等义务。"
        ]
        
        # 初始化模型
        embedding_model = SimpleTextEmbedding()
        
        # 训练模型
        embedding_model.fit(test_docs)
        
        # 测试查询编码
        test_query = "合同违约的法律责任"
        query_embedding = embedding_model.encode_query(test_query)
        logger.info(f"查询编码测试成功: {query_embedding.shape}")
        
        # 测试文档编码
        doc_embeddings = embedding_model.encode_documents(test_docs)
        logger.info(f"文档编码测试成功: {doc_embeddings.shape}")
        
        # 测试相似度计算
        similarities = embedding_model.compute_similarity(query_embedding, doc_embeddings)
        logger.info(f"相似度计算测试成功: {similarities.shape}, 最高相似度: {similarities.max():.3f}")
        
        # 验证向量维度
        expected_max_features = embedding_model.get_embedding_dim()
        logger.info(f"向量维度: {expected_max_features}")
        
        # 测试模型保存和加载
        test_model_path = os.path.join(embedding_model.cache_dir, "test_model.pkl")
        embedding_model.save_model(test_model_path)
        
        # 创建新模型并加载
        new_model = SimpleTextEmbedding()
        new_model.load_model(test_model_path)
        
        # 验证加载的模型
        query_embedding2 = new_model.encode_query(test_query)
        assert np.allclose(query_embedding, query_embedding2), "模型保存/加载后结果不一致"
        
        # 清理测试文件
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        
        logger.info("✅ 简化向量化模型测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 简化向量化模型测试失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    success = test_simple_embedding_model()
    if success:
        print("\n🎉 简化版文本向量化模型测试成功!")
        print("📌 下一步: 可以开始构建向量索引系统")
    else:
        print("\n❌ 测试失败，请检查错误信息")