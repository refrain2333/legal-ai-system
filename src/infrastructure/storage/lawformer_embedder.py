#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lawformer模型编码器
使用thunlp/Lawformer进行法律文本向量化编码
"""

import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer, LongformerModel, LongformerConfig
from typing import List, Union, Optional
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)


class LawformerEmbedder:
    """Lawformer模型编码器 - 提供标准的文本向量化接口"""
    
    def __init__(self, model_name: str = "thunlp/Lawformer", cache_folder: Optional[str] = None):
        self.model_name = model_name
        self.cache_folder = cache_folder
        self.tokenizer = None
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"LawformerEmbedder initialized with device: {self.device}")
        
    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            logger.info(f"Loading Lawformer model: {self.model_name}")
            try:
                # 构建加载参数
                kwargs = {}
                if self.cache_folder:
                    kwargs['cache_dir'] = self.cache_folder
                
                # 尝试使用本地路径直接加载
                model_path = None
                if self.cache_folder:
                    # 检查本地缓存中的模型
                    from pathlib import Path
                    cache_path = Path(self.cache_folder) / "models--thunlp--Lawformer"
                    if cache_path.exists():
                        # 找到最新的snapshot
                        snapshots_dir = cache_path / "snapshots"
                        if snapshots_dir.exists():
                            snapshots = [d for d in snapshots_dir.iterdir() if d.is_dir()]
                            if snapshots:
                                model_path = str(max(snapshots, key=lambda x: x.stat().st_mtime))
                                logger.info(f"Using local model path: {model_path}")
                
                # 加载tokenizer
                if model_path:
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                else:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, **kwargs, trust_remote_code=True)
                
                # 加载模型 - 尝试多种方式
                try:
                    # 方法1: 使用本地路径和trust_remote_code
                    if model_path:
                        self.model = AutoModel.from_pretrained(model_path, trust_remote_code=True)
                        logger.info("Successfully loaded model from local path with trust_remote_code")
                    else:
                        self.model = AutoModel.from_pretrained(self.model_name, trust_remote_code=True, **kwargs)
                        logger.info("Successfully loaded model with trust_remote_code")
                        
                except Exception as e1:
                    logger.warning(f"Failed with trust_remote_code: {e1}")
                    try:
                        # 方法2: 强制使用Longformer类
                        if model_path:
                            self.model = LongformerModel.from_pretrained(model_path)
                            logger.info("Successfully loaded as LongformerModel from local path")
                        else:
                            self.model = LongformerModel.from_pretrained(self.model_name, **kwargs)
                            logger.info("Successfully loaded as LongformerModel")
                            
                    except Exception as e2:
                        logger.warning(f"Failed with LongformerModel: {e2}")
                        # 方法3: 手动指定配置
                        from transformers import LongformerConfig
                        try:
                            if model_path:
                                config = LongformerConfig.from_pretrained(model_path)
                                self.model = LongformerModel.from_pretrained(model_path, config=config)
                                logger.info("Successfully loaded with manual config")
                            else:
                                raise Exception("Need local path for manual config loading")
                        except Exception as e3:
                            logger.error(f"All loading methods failed: {e1}, {e2}, {e3}")
                            raise e1  # 抛出第一个错误
                    
                self.model.to(self.device)
                self.model.eval()
                logger.info("Lawformer model loaded successfully")
                
                # 打印模型信息
                logger.info(f"Model max_position_embeddings: {getattr(self.model.config, 'max_position_embeddings', 'Unknown')}")
                logger.info(f"Model hidden_size: {getattr(self.model.config, 'hidden_size', 'Unknown')}")
                logger.info(f"Model type: {getattr(self.model.config, 'model_type', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"Failed to load Lawformer model: {e}")
                raise
    
    def encode(self, texts: Union[str, List[str]], batch_size: int = 8, max_length: int = 4096, 
               show_progress_bar: bool = True) -> np.ndarray:
        """
        编码文本为向量
        
        Args:
            texts: 输入文本或文本列表
            batch_size: 批处理大小
            max_length: 最大序列长度，Lawformer支持4096
            show_progress_bar: 是否显示进度条
            
        Returns:
            numpy数组，形状为 (n_texts, hidden_size)
        """
        self._load_model()
        
        # 统一处理为列表
        if isinstance(texts, str):
            texts = [texts]
            
        all_embeddings = []
        
        # 批处理
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        
        if show_progress_bar:
            batches = tqdm(batches, desc="Encoding with Lawformer")
            
        with torch.no_grad():
            for batch in batches:
                try:
                    # Tokenize
                    inputs = self.tokenizer(
                        batch,
                        return_tensors="pt",
                        max_length=max_length,
                        truncation=True,
                        padding=True
                    )
                    
                    # 移动到设备
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # 获取模型输出
                    outputs = self.model(**inputs)
                    
                    # 提取句子向量 - 使用[CLS] token (第一个token)
                    embeddings = outputs.last_hidden_state[:, 0, :]  # [batch_size, hidden_size]
                    
                    # 移动回CPU并转换为numpy
                    embeddings = embeddings.cpu().numpy()
                    all_embeddings.append(embeddings)
                    
                except Exception as e:
                    logger.error(f"Error encoding batch: {e}")
                    # 如果批处理失败，尝试单个处理
                    for text in batch:
                        try:
                            single_embedding = self._encode_single(text, max_length)
                            all_embeddings.append(single_embedding.reshape(1, -1))
                        except Exception as single_e:
                            logger.error(f"Failed to encode single text: {single_e}")
                            # 返回零向量作为fallback
                            zero_embedding = np.zeros((1, self.model.config.hidden_size))
                            all_embeddings.append(zero_embedding)
        
        # 合并所有批次的结果
        if all_embeddings:
            result = np.vstack(all_embeddings)
            logger.info(f"Encoded {len(texts)} texts to embeddings of shape {result.shape}")
            return result
        else:
            logger.warning("No embeddings generated, returning zero matrix")
            return np.zeros((len(texts), self.model.config.hidden_size))
    
    def _encode_single(self, text: str, max_length: int = 4096) -> np.ndarray:
        """编码单个文本"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            padding=True
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
        return embedding.flatten()
    
    def get_sentence_embedding_dimension(self) -> int:
        """获取向量维度"""
        self._load_model()
        return self.model.config.hidden_size
        
    def get_max_seq_length(self) -> int:
        """获取最大序列长度"""
        self._load_model()
        return getattr(self.model.config, 'max_position_embeddings', 4096)


# 为了向后兼容，提供一个工厂函数
def create_lawformer_model(model_name: str = "thunlp/Lawformer", cache_folder: Optional[str] = None):
    """创建Lawformer模型实例"""
    return LawformerEmbedder(model_name=model_name, cache_folder=cache_folder)
