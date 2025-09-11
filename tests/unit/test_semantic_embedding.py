#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义向量化模型单元测试
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.semantic_embedding import SemanticTextEmbedding


class TestSemanticEmbedding:
    """语义向量化模型单元测试"""
    
    @pytest.fixture
    def embedding_model(self):
        """提供语义向量化模型实例"""
        return SemanticTextEmbedding()
    
    @pytest.fixture
    def test_texts(self):
        """提供测试文本数据"""
        return [
            "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
            "公司是企业法人，有独立的法人财产，享有法人财产权。",
            "故意伤害他人身体的，处三年以下有期徒刑、拘役或者管制。"
        ]
    
    def test_model_initialization(self, embedding_model):
        """测试模型初始化"""
        assert embedding_model is not None
        assert hasattr(embedding_model, 'model')
    
    def test_query_encoding(self, embedding_model):
        """测试查询编码"""
        query_vector = embedding_model.encode_query("合同违约责任")
        
        # 检查返回值类型和维度
        assert isinstance(query_vector, np.ndarray)
        assert len(query_vector.shape) == 2
        assert query_vector.shape[1] == 768  # 固定的768维向量
    
    def test_document_encoding(self, embedding_model, test_texts):
        """测试文档批量编码"""
        doc_vectors = embedding_model.encode_documents(test_texts)
        
        # 检查返回值类型和维度
        assert isinstance(doc_vectors, np.ndarray)
        assert doc_vectors.shape[0] == len(test_texts)
        assert doc_vectors.shape[1] == 768  # 固定的768维向量
    
    def test_similarity_computation(self, embedding_model):
        """测试相似度计算"""
        query = "合同违约"
        documents = ["合同纠纷处理", "刑法相关条文"]
        
        similarities = embedding_model.compute_similarity(query, documents)
        
        # 检查返回值
        assert isinstance(similarities, np.ndarray)
        assert len(similarities) == len(documents)
        assert all(0 <= sim <= 1 for sim in similarities)