#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法智导航项目 - 完整版数据处理器
处理完整规模的法律数据集 (3000+法条 + 1000+案例)

与simple版本的区别：
- 处理完整的原始数据文件 (18MB+)
- 支持大规模数据集的内存优化
- 增强的数据清理和预处理功能
- 支持增量加载和缓存

作者：Claude Code Assistant
版本：v0.3.0 (完整版)
"""

import pandas as pd
import numpy as np
import os
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pickle


class FullDatasetProcessor:
    """
    完整版数据集处理器
    
    特点：
    - 处理全量法律数据 (3000+法条 + 1000+案例)
    - 内存优化的大数据处理
    - 数据质量检查和清理
    - 支持缓存和增量更新
    """
    
    def __init__(self, data_dir: str = "data/raw"):
        """
        初始化数据处理器
        
        Args:
            data_dir: 原始数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.cache_dir = Path("data/processed")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.files = {
            'laws': self.data_dir / "raw_laws(1).csv",
            'cases': self.data_dir / "raw_cases(1).csv", 
            'mapping_exact': self.data_dir / "精确映射表.csv",
            'mapping_fuzzy': self.data_dir / "精确+模糊匹配映射表.csv"
        }
        
        # 数据统计
        self.stats = {
            'total_documents': 0,
            'law_documents': 0,
            'case_documents': 0,
            'processing_time': 0.0,
            'memory_usage_mb': 0.0,
            'cache_size_mb': 0.0
        }
        
        # 处理后的数据
        self.documents = []
        self.is_loaded = False
    
    def validate_data_files(self) -> Dict[str, bool]:
        """
        验证所有必需的数据文件是否存在
        
        Returns:
            Dict: 文件验证结果
        """
        print("Validating data files...")
        validation_results = {}
        
        for name, file_path in self.files.items():
            exists = file_path.exists()
            validation_results[name] = exists
            
            if exists:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  - {name}: OK ({size_mb:.1f}MB)")
            else:
                print(f"  - {name}: MISSING")
        
        all_valid = all(validation_results.values())
        print(f"Validation result: {'PASSED' if all_valid else 'FAILED'}")
        
        return validation_results
    
    def load_laws_data(self, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        加载法条数据
        
        Args:
            encoding: 文件编码
            
        Returns:
            pd.DataFrame: 法条数据框
        """
        print("Loading laws data...")
        start_time = time.time()
        
        try:
            # 尝试不同编码方式
            for enc in [encoding, 'gbk', 'utf-8-sig']:
                try:
                    df = pd.read_csv(self.files['laws'], encoding=enc)
                    print(f"  - Successfully loaded with {enc} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode laws file with any encoding")
            
            # 数据清理
            df = self._clean_dataframe(df, 'law')
            
            load_time = time.time() - start_time
            print(f"  - Laws loaded: {len(df)} records in {load_time:.2f}s")
            
            return df
            
        except Exception as e:
            print(f"ERROR loading laws data: {str(e)}")
            raise
    
    def load_cases_data(self, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        加载案例数据
        
        Args:
            encoding: 文件编码
            
        Returns:
            pd.DataFrame: 案例数据框
        """
        print("Loading cases data...")
        start_time = time.time()
        
        try:
            # 分块加载大文件以优化内存
            chunk_size = 1000
            chunks = []
            
            # 尝试不同编码方式
            for enc in [encoding, 'gbk', 'utf-8-sig']:
                try:
                    for chunk in pd.read_csv(self.files['cases'], 
                                           encoding=enc, 
                                           chunksize=chunk_size):
                        chunks.append(self._clean_dataframe(chunk, 'case'))
                    print(f"  - Successfully loaded with {enc} encoding")
                    break
                except UnicodeDecodeError:
                    chunks = []  # 重置chunks
                    continue
            else:
                raise ValueError("Could not decode cases file with any encoding")
            
            # 合并所有数据块
            df = pd.concat(chunks, ignore_index=True)
            
            load_time = time.time() - start_time
            print(f"  - Cases loaded: {len(df)} records in {load_time:.2f}s")
            
            return df
            
        except Exception as e:
            print(f"ERROR loading cases data: {str(e)}")
            raise
    
    def _clean_dataframe(self, df: pd.DataFrame, doc_type: str) -> pd.DataFrame:
        """
        清理和标准化数据框
        
        Args:
            df: 原始数据框
            doc_type: 文档类型 ('law' 或 'case')
            
        Returns:
            pd.DataFrame: 清理后的数据框
        """
        # 删除完全空的行
        df = df.dropna(how='all')
        
        # 根据文档类型进行特定清理
        if doc_type == 'law':
            # 法条数据的清理逻辑
            required_columns = self._get_law_columns(df)
        elif doc_type == 'case':
            # 案例数据的清理逻辑
            required_columns = self._get_case_columns(df)
        else:
            required_columns = []
        
        # 确保必需列存在
        for col in required_columns:
            if col not in df.columns:
                print(f"WARNING: Missing expected column '{col}' in {doc_type} data")
        
        # 填充缺失值
        df = df.fillna('')
        
        # 去除多余的空白字符
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _get_law_columns(self, df: pd.DataFrame) -> List[str]:
        """获取法条数据的关键列名"""
        # 根据实际数据结构识别关键列
        possible_title_cols = ['标题', 'title', '条文标题', '法条名称']
        possible_content_cols = ['内容', 'content', '条文内容', '法条内容']
        possible_id_cols = ['id', 'ID', '编号', '条文编号']
        
        title_col = None
        content_col = None
        id_col = None
        
        # 识别标题列
        for col in possible_title_cols:
            if col in df.columns:
                title_col = col
                break
        
        # 识别内容列
        for col in possible_content_cols:
            if col in df.columns:
                content_col = col
                break
        
        # 识别ID列
        for col in possible_id_cols:
            if col in df.columns:
                id_col = col
                break
        
        return [col for col in [title_col, content_col, id_col] if col is not None]
    
    def _get_case_columns(self, df: pd.DataFrame) -> List[str]:
        """获取案例数据的关键列名"""
        # 根据实际数据结构识别关键列
        possible_title_cols = ['案件名称', 'title', '标题', '案例标题']
        possible_content_cols = ['案例内容', 'content', '内容', '判决书内容']
        possible_id_cols = ['id', 'ID', '编号', '案例编号']
        
        title_col = None
        content_col = None
        id_col = None
        
        # 识别标题列
        for col in possible_title_cols:
            if col in df.columns:
                title_col = col
                break
        
        # 识别内容列
        for col in possible_content_cols:
            if col in df.columns:
                content_col = col
                break
        
        # 识别ID列
        for col in possible_id_cols:
            if col in df.columns:
                id_col = col
                break
        
        return [col for col in [title_col, content_col, id_col] if col is not None]
    
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """
        处理所有文档数据
        
        Returns:
            List[Dict]: 标准化的文档列表
        """
        if self.is_loaded:
            return self.documents
        
        print("=" * 60)
        print("Processing Full Legal Dataset")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. 验证数据文件
            validation = self.validate_data_files()
            if not all(validation.values()):
                raise ValueError("Some required data files are missing")
            
            # 2. 加载法条数据
            laws_df = self.load_laws_data()
            
            # 3. 加载案例数据
            cases_df = self.load_cases_data()
            
            # 4. 转换为标准格式
            print("Converting to standard format...")
            documents = []
            
            # 处理法条
            law_docs = self._convert_laws_to_documents(laws_df)
            documents.extend(law_docs)
            
            # 处理案例
            case_docs = self._convert_cases_to_documents(cases_df)
            documents.extend(case_docs)
            
            # 5. 更新统计信息
            processing_time = time.time() - start_time
            self.stats.update({
                'total_documents': len(documents),
                'law_documents': len(law_docs),
                'case_documents': len(case_docs),
                'processing_time': processing_time,
                'memory_usage_mb': self._estimate_memory_usage(documents)
            })
            
            print(f"\\nProcessing completed!")
            print(f"  - Total documents: {self.stats['total_documents']}")
            print(f"  - Law documents: {self.stats['law_documents']}")
            print(f"  - Case documents: {self.stats['case_documents']}")
            print(f"  - Processing time: {processing_time:.2f}s")
            print(f"  - Estimated memory: {self.stats['memory_usage_mb']:.1f}MB")
            
            self.documents = documents
            self.is_loaded = True
            
            return documents
            
        except Exception as e:
            print(f"ERROR processing documents: {str(e)}")
            raise
    
    def _convert_laws_to_documents(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """将法条数据框转换为标准文档格式"""
        documents = []
        
        # 识别关键列
        columns = list(df.columns)
        print(f"Law columns: {columns}")
        
        for idx, row in df.iterrows():
            # 尝试提取标题和内容
            title = self._extract_field(row, ['标题', 'title', '条文标题', '法条名称']) or f"法条_{idx}"
            content = self._extract_field(row, ['内容', 'content', '条文内容', '法条内容']) or ""
            doc_id = self._extract_field(row, ['id', 'ID', '编号', '条文编号']) or f"law_{idx:06d}"
            
            # 合并标题和内容作为检索文本
            full_text = f"{title}\\n{content}".strip()
            
            if full_text:  # 只保留有内容的文档
                documents.append({
                    'id': str(doc_id),
                    'type': 'law',
                    'title': str(title),
                    'content': str(content), 
                    'full_text': full_text,
                    'metadata': {
                        'source': 'raw_laws(1).csv',
                        'row_index': idx,
                        'original_columns': columns
                    }
                })
        
        return documents
    
    def _convert_cases_to_documents(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """将案例数据框转换为标准文档格式"""
        documents = []
        
        # 识别关键列
        columns = list(df.columns)
        print(f"Case columns: {columns}")
        
        for idx, row in df.iterrows():
            # 尝试提取标题和内容
            title = self._extract_field(row, ['案件名称', 'title', '标题', '案例标题']) or f"案例_{idx}"
            content = self._extract_field(row, ['案例内容', 'content', '内容', '判决书内容']) or ""
            doc_id = self._extract_field(row, ['id', 'ID', '编号', '案例编号']) or f"case_{idx:06d}"
            
            # 合并标题和内容作为检索文本
            full_text = f"{title}\\n{content}".strip()
            
            if full_text:  # 只保留有内容的文档
                documents.append({
                    'id': str(doc_id),
                    'type': 'case',
                    'title': str(title),
                    'content': str(content),
                    'full_text': full_text,
                    'metadata': {
                        'source': 'raw_cases(1).csv',
                        'row_index': idx,
                        'original_columns': columns
                    }
                })
        
        return documents
    
    def _extract_field(self, row: pd.Series, possible_columns: List[str]) -> Optional[str]:
        """从行中提取指定字段的值"""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                return str(row[col]).strip()
        return None
    
    def _estimate_memory_usage(self, documents: List[Dict]) -> float:
        """估算文档列表的内存使用量 (MB)"""
        if not documents:
            return 0.0
        
        # 估算单个文档的平均大小
        sample_doc = documents[0]
        sample_size = len(str(sample_doc).encode('utf-8'))
        
        # 估算总内存使用
        total_size_bytes = sample_size * len(documents)
        return total_size_bytes / (1024 * 1024)
    
    def save_processed_data(self, cache_name: str = "full_dataset.pkl") -> str:
        """
        保存处理后的数据到缓存
        
        Args:
            cache_name: 缓存文件名
            
        Returns:
            str: 缓存文件路径
        """
        if not self.is_loaded:
            raise ValueError("No data loaded to save")
        
        cache_path = self.cache_dir / cache_name
        
        try:
            cache_data = {
                'documents': self.documents,
                'stats': self.stats,
                'version': '0.3.0',
                'created_at': time.time()
            }
            
            print(f"Saving processed data to {cache_path}...")
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            cache_size = cache_path.stat().st_size / (1024 * 1024)
            self.stats['cache_size_mb'] = cache_size
            
            print(f"  - Cache saved: {cache_size:.1f}MB")
            
            return str(cache_path)
            
        except Exception as e:
            print(f"ERROR saving cache: {str(e)}")
            raise
    
    def load_processed_data(self, cache_name: str = "full_dataset.pkl") -> bool:
        """
        从缓存加载处理后的数据
        
        Args:
            cache_name: 缓存文件名
            
        Returns:
            bool: 加载是否成功
        """
        cache_path = self.cache_dir / cache_name
        
        if not cache_path.exists():
            return False
        
        try:
            print(f"Loading processed data from {cache_path}...")
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.documents = cache_data.get('documents', [])
            self.stats = cache_data.get('stats', {})
            self.is_loaded = len(self.documents) > 0
            
            cache_size = cache_path.stat().st_size / (1024 * 1024)
            
            print(f"  - Cache loaded: {len(self.documents)} documents, {cache_size:.1f}MB")
            
            return True
            
        except Exception as e:
            print(f"ERROR loading cache: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据处理统计信息"""
        return self.stats.copy()


def test_full_dataset_processor():
    """测试完整数据集处理器"""
    print("=" * 60)
    print("Full Dataset Processor Test")
    print("=" * 60)
    
    try:
        # 创建处理器实例
        processor = FullDatasetProcessor()
        
        # 尝试从缓存加载
        if processor.load_processed_data():
            print("Data loaded from cache successfully!")
        else:
            print("No cache found, processing raw data...")
            # 处理原始数据
            documents = processor.process_all_documents()
            # 保存缓存
            processor.save_processed_data()
        
        # 显示统计信息
        stats = processor.get_stats()
        print("\\nDataset Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  - {key}: {value:.3f}")
            else:
                print(f"  - {key}: {value}")
        
        # 显示样本数据
        if processor.documents:
            print("\\nSample Documents:")
            for i, doc in enumerate(processor.documents[:3]):
                print(f"\\n{i+1}. [{doc['type']}] {doc['title'][:50]}...")
                print(f"   Content: {doc['content'][:100]}...")
        
        print("\\nFull dataset processing test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\\nTest failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_full_dataset_processor()
    
    if success:
        print("\\nReady to build full-scale vector index!")
    else:
        print("\\nNeed to fix data processing issues")