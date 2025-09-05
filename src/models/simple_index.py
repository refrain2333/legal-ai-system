#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版向量索引系统
使用scikit-learn实现基本的向量检索功能
支持从CSV数据构建索引和高效检索
"""

import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.utils.logger import setup_logger
from src.models.simple_embedding import SimpleTextEmbedding

logger = setup_logger(__name__)

class SimpleVectorIndex:
    """简化版向量索引管理类"""
    
    def __init__(self):
        """初始化向量索引"""
        self.embedding_model = None
        self.document_vectors = None  # 存储文档向量矩阵
        self.metadata = []  # 存储文档元信息
        self.id_to_idx = {}  # 文档ID到索引的映射
        
        logger.info("简化向量索引已初始化")

    def build_from_data(self, 
                       laws_path: str = None,
                       cases_path: str = None) -> bool:
        """
        从CSV数据文件构建向量索引
        
        Args:
            laws_path: 法律条文CSV路径
            cases_path: 案例CSV路径
            
        Returns:
            构建是否成功
        """
        try:
            # 使用默认路径
            laws_path = laws_path or os.path.join(settings.DATA_RAW_PATH, "raw_laws(1).csv")
            cases_path = cases_path or os.path.join(settings.DATA_RAW_PATH, "raw_cases(1).csv")
            
            logger.info("开始构建向量索引...")
            
            # 1. 加载和处理法律条文数据
            laws_data = self._load_laws_data(laws_path)
            logger.info(f"加载法律条文: {len(laws_data)} 条")
            
            # 2. 加载和处理案例数据  
            cases_data = self._load_cases_data(cases_path)
            logger.info(f"加载案例数据: {len(cases_data)} 个")
            
            # 3. 合并数据
            all_documents = laws_data + cases_data
            logger.info(f"总文档数: {len(all_documents)}")
            
            # 4. 初始化嵌入模型
            self.embedding_model = SimpleTextEmbedding()
            
            # 5. 提取文本内容进行向量化
            texts = [doc['content'] for doc in all_documents]
            
            # 6. 训练向量化模型并生成向量
            logger.info("开始训练向量化模型...")
            self.embedding_model.fit(texts)
            
            logger.info("开始向量化文档...")
            self.document_vectors = self.embedding_model.encode_documents(texts)
            
            # 7. 构建索引
            self._build_index(all_documents)
            
            logger.info("向量索引构建完成")
            return True
            
        except Exception as e:
            logger.error(f"索引构建失败: {e}")
            return False

    def _load_laws_data(self, file_path: str) -> List[Dict]:
        """加载法律条文数据"""
        try:
            logger.info(f"正在加载法律条文: {file_path}")
            df = pd.read_csv(file_path, encoding='utf-8')
            logger.info(f"法律条文CSV列名: {list(df.columns)}")
            
            laws = []
            for idx, row in df.iterrows():
                # 根据实际CSV结构调整字段名
                law_id = f"law_{idx:06d}"
                
                # 安全获取字段值
                title = str(row.get('法律名称', '') or row.get('title', '') or f'法条{idx+1}')
                content = str(row.get('条文内容', '') or row.get('content', ''))
                
                # 跳过空内容
                if not content.strip():
                    logger.warning(f"跳过空内容的法条: {law_id}")
                    continue
                
                laws.append({
                    'id': law_id,
                    'type': 'law',
                    'title': title,
                    'content': content,
                    'source': 'laws_csv',
                    'publish_date': str(row.get('发布日期', '')),
                    'status': str(row.get('效力状态', ''))
                })
                
                # 限制加载数量以节省内存和时间
                if len(laws) >= 100:  # 先加载100条进行测试
                    logger.info("为节省时间，当前只加载前100条法律条文")
                    break
                    
            return laws
            
        except Exception as e:
            logger.error(f"加载法律条文数据失败: {e}")
            raise

    def _load_cases_data(self, file_path: str) -> List[Dict]:
        """加载案例数据"""
        try:
            logger.info(f"正在加载案例数据: {file_path}")
            df = pd.read_csv(file_path, encoding='utf-8')
            logger.info(f"案例CSV列名: {list(df.columns)}")
            
            cases = []
            for idx, row in df.iterrows():
                # 根据实际CSV结构调整字段名
                case_id = f"case_{idx:06d}"
                
                # 安全获取字段值
                title = str(row.get('案例标题', '') or row.get('title', '') or f'案例{idx+1}')
                
                # 优先使用案件描述，如果没有则使用其他字段
                content = str(row.get('案件描述', '') or 
                            row.get('基本案情', '') or 
                            row.get('content', ''))
                
                # 跳过空内容
                if not content.strip():
                    logger.warning(f"跳过空内容的案例: {case_id}")
                    continue
                
                cases.append({
                    'id': case_id,
                    'type': 'case', 
                    'title': title,
                    'content': content,
                    'source': 'cases_csv',
                    'case_type': str(row.get('案件类型', '')),
                    'court_level': str(row.get('法院级别', ''))
                })
                
                # 限制加载数量以节省内存和时间
                if len(cases) >= 50:  # 先加载50个案例进行测试
                    logger.info("为节省时间，当前只加载前50个案例")
                    break
                
            return cases
            
        except Exception as e:
            logger.error(f"加载案例数据失败: {e}")
            raise

    def _build_index(self, documents: List[Dict]):
        """构建索引映射"""
        try:
            # 保存元数据
            self.metadata = documents
            
            # 构建ID到索引的映射
            self.id_to_idx = {doc['id']: idx for idx, doc in enumerate(documents)}
            
            logger.info(f"索引构建完成，包含 {len(documents)} 个文档")
            
        except Exception as e:
            logger.error(f"索引构建失败: {e}")
            raise

    def search(self, 
               query: str, 
               top_k: int = 10,
               min_similarity: float = 0.0) -> List[Dict]:
        """
        向量检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            
        Returns:
            检索结果列表
        """
        try:
            if self.document_vectors is None or self.embedding_model is None:
                logger.warning("索引未构建，无法检索")
                return []
            
            logger.info(f"开始检索查询: '{query[:50]}...' (Top-{top_k})")
            
            # 1. 将查询转换为向量
            query_vector = self.embedding_model.encode_query(query)
            
            # 2. 计算与所有文档的相似度
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]
            
            # 3. 获取相似度最高的文档索引
            # 排序并获取top_k个结果
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # 4. 格式化结果
            results = []
            for rank, idx in enumerate(top_indices):
                similarity = similarities[idx]
                
                # 应用最小相似度过滤
                if similarity < min_similarity:
                    break
                    
                doc = self.metadata[idx].copy()
                doc['score'] = float(similarity)
                doc['rank'] = rank + 1
                
                results.append(doc)
            
            logger.info(f"检索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """根据ID获取文档"""
        try:
            if doc_id not in self.id_to_idx:
                return None
            
            idx = self.id_to_idx[doc_id]
            return self.metadata[idx].copy()
            
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        if not self.metadata:
            return {}
        
        law_count = sum(1 for doc in self.metadata if doc['type'] == 'law')
        case_count = sum(1 for doc in self.metadata if doc['type'] == 'case')
        
        return {
            'total_documents': len(self.metadata),
            'law_documents': law_count,
            'case_documents': case_count,
            'vector_dimension': self.document_vectors.shape[1] if self.document_vectors is not None else 0,
            'model_vocabulary_size': self.embedding_model.get_embedding_dim() if self.embedding_model else 0
        }

    def save_index(self, save_dir: str):
        """保存索引到磁盘"""
        try:
            os.makedirs(save_dir, exist_ok=True)
            
            # 保存向量矩阵
            vectors_path = os.path.join(save_dir, "document_vectors.npy")
            np.save(vectors_path, self.document_vectors)
            
            # 保存元数据
            metadata_path = os.path.join(save_dir, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            # 保存ID映射
            mapping_path = os.path.join(save_dir, "id_mapping.json")
            with open(mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.id_to_idx, f, ensure_ascii=False, indent=2)
            
            # 保存向量化模型
            model_path = os.path.join(save_dir, "embedding_model.pkl")
            self.embedding_model.save_model(model_path)
            
            logger.info(f"索引已保存到: {save_dir}")
            
        except Exception as e:
            logger.error(f"索引保存失败: {e}")
            raise

    def load_index(self, load_dir: str) -> bool:
        """从磁盘加载索引"""
        try:
            # 加载向量矩阵
            vectors_path = os.path.join(load_dir, "document_vectors.npy")
            if not os.path.exists(vectors_path):
                logger.error(f"向量文件不存在: {vectors_path}")
                return False
            
            self.document_vectors = np.load(vectors_path)
            
            # 加载元数据
            metadata_path = os.path.join(load_dir, "metadata.json")
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            # 加载ID映射
            mapping_path = os.path.join(load_dir, "id_mapping.json")
            with open(mapping_path, 'r', encoding='utf-8') as f:
                self.id_to_idx = json.load(f)
            
            # 加载向量化模型
            model_path = os.path.join(load_dir, "embedding_model.pkl")
            self.embedding_model = SimpleTextEmbedding()
            self.embedding_model.load_model(model_path)
            
            logger.info(f"索引加载成功，包含 {len(self.metadata)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"索引加载失败: {e}")
            return False

# 测试函数
def test_simple_vector_index():
    """测试简化版向量索引系统"""
    try:
        logger.info("开始测试简化向量索引系统...")
        
        # 创建索引
        index = SimpleVectorIndex()
        
        # 构建索引（使用实际数据）
        success = index.build_from_data()
        if not success:
            logger.error("索引构建失败")
            return False
        
        # 打印统计信息
        stats = index.get_statistics()
        logger.info(f"索引统计信息: {stats}")
        
        # 测试查询
        test_queries = [
            "合同违约责任",
            "故意伤害",
            "公司法人财产权"
        ]
        
        for query in test_queries:
            logger.info(f"\n测试查询: '{query}'")
            results = index.search(query, top_k=3)
            
            for i, result in enumerate(results):
                logger.info(f"  {i+1}. [{result['type']}] {result['title'][:50]}... (相似度: {result['score']:.3f})")
        
        # 测试根据ID获取文档
        if index.metadata:
            test_id = index.metadata[0]['id']
            doc = index.get_document_by_id(test_id)
            if doc:
                logger.info(f"根据ID获取文档成功: {doc['id']} - {doc['title'][:50]}...")
        
        # 测试索引保存和加载
        test_index_dir = os.path.join(settings.INDEX_STORAGE_PATH, "test_index")
        logger.info(f"测试保存索引到: {test_index_dir}")
        index.save_index(test_index_dir)
        
        # 创建新索引并加载
        new_index = SimpleVectorIndex()
        load_success = new_index.load_index(test_index_dir)
        if load_success:
            # 验证加载后的功能
            test_results = new_index.search("合同", top_k=2)
            logger.info(f"加载后测试查询成功，返回 {len(test_results)} 个结果")
        
        logger.info("简化向量索引系统测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"简化向量索引系统测试失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    success = test_simple_vector_index()
    if success:
        print("\n简化版向量索引系统测试成功!")
        print("下一步: 可以开始实现语义检索服务")
    else:
        print("\n测试失败，请检查错误信息")