#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调增强版Lawformer嵌入器
使用对比学习微调的模型进行向量编码
"""

import os
import torch
import torch.nn as nn
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)


class LawformerContrastiveModel(nn.Module):
    """Lawformer对比学习模型 - 与训练时的架构保持一致"""

    def __init__(self, model_name: str = "thunlp/Lawformer",
                 embedding_dim: int = 768, temperature: float = 0.07):
        super().__init__()
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.temperature = temperature

        # 加载预训练模型
        if os.path.exists(model_name):
            # 本地模型路径
            self.backbone = AutoModel.from_pretrained(model_name, local_files_only=True)
        else:
            # 在线模型名称
            self.backbone = AutoModel.from_pretrained(model_name)

        # 投影头 (与训练时保持一致 - 根据实际模型文件调整)
        self.projection_head = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),  # 768 -> 768
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim)   # 768 -> 768
        )

    def forward(self, input_ids, attention_mask):
        """前向传播"""
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        projected = self.projection_head(embeddings)
        return projected


class FineTunedLawformerEmbedder:
    """微调增强版Lawformer嵌入器"""

    def __init__(self, base_model_path: str, fine_tuned_model_path: str,
                 use_fine_tuned: bool = True, device: Optional[str] = None):
        """
        初始化微调增强版嵌入器

        Args:
            base_model_path: 基础Lawformer模型路径
            fine_tuned_model_path: 微调模型权重路径
            use_fine_tuned: 是否使用微调模型
            device: 设备类型，None表示自动选择
        """
        self.base_model_path = base_model_path
        self.fine_tuned_model_path = fine_tuned_model_path
        self.use_fine_tuned = use_fine_tuned

        # 设备选择
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        logger.info(f"Using device: {self.device}")

        self.tokenizer = None
        self.model = None
        self.loaded = False

    def load_model(self) -> bool:
        """加载模型和tokenizer"""
        if self.loaded:
            return True

        try:
            logger.info("Loading tokenizer and model...")

            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)

            if self.use_fine_tuned and Path(self.fine_tuned_model_path).exists():
                # 加载微调模型
                logger.info("Loading fine-tuned enhanced model...")
                self.model = LawformerContrastiveModel(
                    model_name=self.base_model_path,
                    embedding_dim=768,
                    temperature=0.07
                )

                # 加载微调权重
                checkpoint = torch.load(self.fine_tuned_model_path, map_location='cpu')

                if 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    epoch = checkpoint.get('epoch', 'unknown')
                    loss = checkpoint.get('loss', 'unknown')
                    logger.info(f"Fine-tuned model loaded successfully (Epoch: {epoch}, Loss: {loss})")
                else:
                    self.model.load_state_dict(checkpoint)
                    logger.info("Fine-tuned model loaded successfully (direct weights)")

                self.model.to(self.device)
                self.model.eval()

            else:
                # 使用基础模型
                logger.info("Loading base Lawformer model...")
                self.model = AutoModel.from_pretrained(self.base_model_path)
                self.model.to(self.device)
                self.model.eval()

            # 设置环境
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'

            self.loaded = True
            logger.info("Model loaded successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def encode_text(self, text: str, max_length: int = 128) -> Optional[np.ndarray]:
        """
        编码单个文本为向量

        Args:
            text: 输入文本
            max_length: 最大序列长度

        Returns:
            文本向量，失败返回None
        """
        if not self.loaded:
            if not self.load_model():
                return None

        try:
            # 编码文本
            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=max_length,
                return_tensors='pt'
            )

            # 移动到设备
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)

            # 获取向量表示
            with torch.no_grad():
                if self.use_fine_tuned and hasattr(self.model, 'backbone'):
                    # 微调模型 - 直接通过forward方法
                    embeddings = self.model(input_ids, attention_mask)
                else:
                    # 基础模型
                    outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                    embeddings = outputs.last_hidden_state[:, 0, :]  # [CLS] token

            # 转换为numpy数组
            vector = embeddings.cpu().numpy()

            return vector

        except Exception as e:
            logger.error(f"Text encoding failed: {e}")
            return None

    def encode_batch(self, texts: list, max_length: int = 128, batch_size: int = 8) -> Optional[np.ndarray]:
        """
        批量编码文本为向量

        Args:
            texts: 文本列表
            max_length: 最大序列长度
            batch_size: 批处理大小

        Returns:
            向量矩阵，失败返回None
        """
        if not texts:
            return None

        if not self.loaded:
            if not self.load_model():
                return None

        try:
            all_vectors = []

            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]

                # 批量编码
                encodings = self.tokenizer(
                    batch_texts,
                    truncation=True,
                    padding='max_length',
                    max_length=max_length,
                    return_tensors='pt'
                )

                # 移动到设备
                input_ids = encodings['input_ids'].to(self.device)
                attention_mask = encodings['attention_mask'].to(self.device)

                # 获取向量表示
                with torch.no_grad():
                    if self.use_fine_tuned and hasattr(self.model, 'backbone'):
                        # 微调模型
                        embeddings = self.model(input_ids, attention_mask)
                    else:
                        # 基础模型
                        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                        embeddings = outputs.last_hidden_state[:, 0, :]  # [CLS] token

                # 添加到结果
                batch_vectors = embeddings.cpu().numpy()
                all_vectors.append(batch_vectors)

            # 合并所有批次
            return np.vstack(all_vectors)

        except Exception as e:
            logger.error(f"Batch encoding failed: {e}")
            return None

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'base_model_path': self.base_model_path,
            'fine_tuned_model_path': self.fine_tuned_model_path,
            'use_fine_tuned': self.use_fine_tuned,
            'device': str(self.device),
            'loaded': self.loaded,
            'model_type': 'fine_tuned_contrastive' if self.use_fine_tuned else 'base_lawformer'
        }

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ========== 兼容性方法 ==========
    def encode(self, text: str, **kwargs) -> Optional[np.ndarray]:
        """
        兼容性方法：编码单个文本

        Args:
            text: 输入文本
            **kwargs: 其他参数

        Returns:
            文本向量
        """
        max_length = kwargs.get('max_length', 128)
        result = self.encode_text(text, max_length)
        if result is not None:
            # 确保返回1D向量，并验证形状
            if result.ndim == 2:
                return result.flatten()  # 转换为1D
            elif result.ndim == 1:
                return result
            else:
                logger.warning(f"Unexpected vector shape: {result.shape}")
                return result.flatten()
        return None