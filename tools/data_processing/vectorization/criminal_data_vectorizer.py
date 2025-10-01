#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
刑事数据向量化处理器
使用Lawformer模型分别对刑法条文和案例进行向量化
"""

import sys
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import time
# 导入自定义的Lawformer适配器
try:
    from src.infrastructure.storage.lawformer_embedder import LawformerEmbedder
    LAWFORMER_AVAILABLE = True
except ImportError:
    LAWFORMER_AVAILABLE = False

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class CriminalDataVectorizer:
    """刑事数据向量化器"""
    
    def __init__(self, model_name: str = "thunlp/Lawformer"):
        """
        初始化向量化器
        
        Args:
            model_name: 使用的预训练模型名称
        """
        self.model_name = model_name
        self.model = None
        self.criminal_articles = []
        self.criminal_cases = []
        
        print(f"初始化向量化器，使用模型: {model_name}")
    
    def load_model(self):
        """加载预训练模型"""
        print(f"加载模型: {self.model_name}...")
        start_time = time.time()
        
        # 根据模型名称选择加载方式
        if LAWFORMER_AVAILABLE:
            print("使用Lawformer适配器...")
            self.model = LawformerEmbedder(model_name=self.model_name)
        else:
            raise ImportError("LawformerEmbedder not available. Please ensure src.infrastructure.storage.lawformer_embedder is accessible.")
        
        load_time = time.time() - start_time
        print(f"模型加载完成，耗时: {load_time:.2f}秒")
        
        # 获取向量维度
        if hasattr(self.model, 'get_sentence_embedding_dimension'):
            try:
                dim = self.model.get_sentence_embedding_dimension()
            except Exception:
                dim = "Unknown"
        else:
            dim = "Unknown"
        print(f"模型维度: {dim}")
    
    def load_criminal_data(self):
        """加载刑事数据"""
        print("加载刑事数据...")
        
        data_dir = Path("data/processed/criminal")
        
        # 加载刑法条文
        articles_file = data_dir / "criminal_articles.pkl"
        with open(articles_file, 'rb') as f:
            self.criminal_articles = pickle.load(f)
        print(f"加载刑法条文: {len(self.criminal_articles)} 个")
        
        # 加载刑事案例
        cases_file = data_dir / "criminal_cases.pkl"
        with open(cases_file, 'rb') as f:
            self.criminal_cases = pickle.load(f)
        print(f"加载刑事案例: {len(self.criminal_cases)} 个")
    
    def prepare_article_texts(self) -> List[str]:
        """准备条文文本用于向量化"""
        print("准备条文文本...")
        
        texts = []
        for article in self.criminal_articles:
            # 组合标题和内容作为完整文本
            if hasattr(article, 'title') and hasattr(article, 'content'):
                full_text = f"{article.title}\n{article.content}"
            elif hasattr(article, 'content'):
                full_text = article.content
            else:
                # 如果是字典格式
                title = article.get('title', '')
                content = article.get('content', '')
                full_text = f"{title}\n{content}" if title else content
            
            texts.append(full_text.strip())
        
        print(f"准备完成，共{len(texts)}个条文文本")
        
        # 显示文本样本
        if texts:
            print(f"文本样本: {texts[0][:100]}...")
        
        return texts
    
    def prepare_case_texts(self) -> List[str]:
        """准备案例文本用于向量化"""
        print("准备案例文本...")
        
        texts = []
        for case in self.criminal_cases:
            # 组合事实描述和罪名作为完整文本
            if hasattr(case, 'fact') and hasattr(case, 'accusations'):
                fact = case.fact if case.fact else ""
                accusations = ", ".join(case.accusations) if case.accusations else ""
                full_text = f"{fact}\n罪名: {accusations}" if accusations else fact
            elif hasattr(case, 'fact'):
                full_text = case.fact
            else:
                # 如果是字典格式
                fact = case.get('fact', '')
                accusations = case.get('accusations', [])
                accusations_str = ", ".join(accusations) if accusations else ""
                full_text = f"{fact}\n罪名: {accusations_str}" if accusations_str else fact
            
            texts.append(full_text.strip() if full_text else "")
        
        # 过滤空文本
        non_empty_texts = [text for text in texts if text.strip()]
        
        print(f"准备完成，共{len(non_empty_texts)}个案例文本（过滤{len(texts) - len(non_empty_texts)}个空文本）")
        
        # 显示文本样本
        if non_empty_texts:
            print(f"文本样本: {non_empty_texts[0][:100]}...")
        
        return non_empty_texts
    
    def vectorize_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        批量向量化文本
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            向量矩阵 (n_texts, embedding_dim)
        """
        print(f"开始向量化，文本数量: {len(texts)}, 批大小: {batch_size}")
        
        start_time = time.time()
        
        # 使用sentence_transformers进行批量编码
        embeddings = self.model.encode(
            texts, 
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        processing_time = time.time() - start_time
        
        print(f"向量化完成")
        print(f"处理时间: {processing_time:.2f}秒")
        print(f"向量矩阵形状: {embeddings.shape}")
        print(f"平均每个文本耗时: {processing_time/len(texts)*1000:.2f}ms")
        
        return embeddings
    
    def save_vectors(self, vectors: np.ndarray, metadata: List[Dict], 
                     output_path: str, data_type: str):
        """
        保存向量和元数据
        
        Args:
            vectors: 向量矩阵
            metadata: 元数据列表
            output_path: 输出路径
            data_type: 数据类型（articles/cases）
        """
        print(f"保存{data_type}向量到: {output_path}")
        
        # 创建保存数据结构
        vector_data = {
            'vectors': vectors,
            'metadata': metadata,
            'model_name': self.model_name,
            'embedding_dim': vectors.shape[1],
            'total_count': vectors.shape[0],
            'data_type': data_type,
            'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': {
                'vector_shape': vectors.shape,
                'vector_dtype': str(vectors.dtype),
                'mean_norm': float(np.linalg.norm(vectors, axis=1).mean()),
                'std_norm': float(np.linalg.norm(vectors, axis=1).std()),
            }
        }
        
        # 保存为pickle格式
        with open(output_path, 'wb') as f:
            pickle.dump(vector_data, f)
        
        # 计算文件大小
        file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
        print(f"保存完成，文件大小: {file_size:.2f}MB")
        
        return vector_data
    
    def create_article_metadata(self) -> List[Dict]:
        """创建条文元数据"""
        metadata = []
        for i, article in enumerate(self.criminal_articles):
            if hasattr(article, 'article_number'):
                # 对象格式
                meta = {
                    'id': f"article_{article.article_number}",
                    'index': i,
                    'article_number': article.article_number,
                    'title': getattr(article, 'title', ''),
                    'chapter': getattr(article, 'chapter', ''),
                    'section': getattr(article, 'section', ''),
                    'content_length': len(getattr(article, 'content', '')),
                    'type': 'criminal_article'
                }
            else:
                # 字典格式
                meta = {
                    'id': f"article_{article.get('article_number', i)}",
                    'index': i,
                    'article_number': article.get('article_number'),
                    'title': article.get('title', ''),
                    'chapter': article.get('chapter', ''),
                    'section': article.get('section', ''),
                    'content_length': len(article.get('content', '')),
                    'type': 'criminal_article'
                }
            metadata.append(meta)
        
        return metadata
    
    def create_case_metadata(self) -> List[Dict]:
        """创建案例元数据"""
        metadata = []
        valid_index = 0
        
        for i, case in enumerate(self.criminal_cases):
            # 检查案例是否有有效内容
            fact = case.fact if hasattr(case, 'fact') else case.get('fact', '')
            if not fact or not fact.strip():
                continue  # 跳过空案例
            
            if hasattr(case, 'case_id'):
                # 对象格式
                meta = {
                    'id': f"case_{case.case_id}",
                    'index': valid_index,
                    'case_id': case.case_id,
                    'accusations': getattr(case, 'accusations', []),
                    'relevant_articles': getattr(case, 'relevant_articles', []),
                    'sentence_months': getattr(case, 'sentence_months', 0),
                    'fine_amount': getattr(case, 'fine_amount', 0),
                    'fact_length': len(fact),
                    'type': 'criminal_case'
                }
            else:
                # 字典格式
                meta = {
                    'id': f"case_{case.get('case_id', i)}",
                    'index': valid_index,
                    'case_id': case.get('case_id', i),
                    'accusations': case.get('accusations', []),
                    'relevant_articles': case.get('relevant_articles', []),
                    'sentence_months': case.get('sentence_months', 0),
                    'fine_amount': case.get('fine_amount', 0),
                    'fact_length': len(fact),
                    'type': 'criminal_case'
                }
            
            metadata.append(meta)
            valid_index += 1
        
        return metadata
    
    def process_all_data(self):
        """处理所有刑事数据的向量化"""
        print("=" * 60)
        print("刑事数据向量化处理器")
        print("=" * 60)
        
        # 1. 加载模型
        self.load_model()
        
        # 2. 加载数据
        self.load_criminal_data()
        
        # 3. 处理条文向量化
        print("\n" + "=" * 40)
        print("处理刑法条文向量化")
        print("=" * 40)
        
        article_texts = self.prepare_article_texts()
        if article_texts:
            article_vectors = self.vectorize_texts(article_texts)
            article_metadata = self.create_article_metadata()
            
            output_dir = Path("data/processed/criminal")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            article_output = output_dir / "criminal_articles_vectors.pkl"
            self.save_vectors(article_vectors, article_metadata, 
                            str(article_output), "criminal_articles")
        
        # 4. 处理案例向量化
        print("\n" + "=" * 40)
        print("处理刑事案例向量化")
        print("=" * 40)
        
        case_texts = self.prepare_case_texts()
        if case_texts:
            case_vectors = self.vectorize_texts(case_texts)
            case_metadata = self.create_case_metadata()
            
            case_output = output_dir / "criminal_cases_vectors.pkl"
            self.save_vectors(case_vectors, case_metadata, 
                            str(case_output), "criminal_cases")
        
        print("\n" + "=" * 60)
        print("向量化处理完成！")
        print("=" * 60)
        
        # 显示统计信息
        total_vectors = len(article_texts) + len(case_texts)
        print(f"总处理文档数: {total_vectors}")
        print(f"  - 刑法条文: {len(article_texts)}")
        print(f"  - 刑事案例: {len(case_texts)}")
        
        return {
            'articles_count': len(article_texts),
            'cases_count': len(case_texts),
            'total_count': total_vectors,
            'model_name': self.model_name
        }

def main():
    """主函数"""
    vectorizer = CriminalDataVectorizer()
    result = vectorizer.process_all_data()
    
    print("\n处理结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()