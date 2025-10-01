#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query2doc增强器
通过LLM生成假设性法律文档片段来增强用户查询，提升语义搜索效果
"""

import logging
from typing import Optional
from src.infrastructure.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)

class Query2docEnhancer:
    """Query2doc查询增强器

    核心思想：将用户的口语化查询转换为专业的法律文档片段，
    然后用这个生成的文档片段进行向量搜索，以提升匹配准确度。
    """

    def __init__(self, llm_client: LLMClient, config):
        """
        初始化Query2doc增强器

        Args:
            llm_client: LLM客户端实例
            config: 配置对象，包含提示词模板和参数
        """
        self.llm_client = llm_client
        self.config = config

        # 从配置获取提示词模板和参数
        self.prompt_template = config.QUERY2DOC_PROMPT_TEMPLATE
        self.max_tokens = config.QUERY2DOC_MAX_TOKENS
        self.temperature = config.QUERY2DOC_TEMPERATURE
        self.enabled = config.ENABLE_QUERY2DOC

        logger.info(f"Query2doc增强器初始化完成，启用状态: {self.enabled}")

    async def enhance_query(self, user_query: str) -> str:
        """
        使用Query2doc技术增强用户查询

        Args:
            user_query: 用户原始查询

        Returns:
            增强后的查询文本，格式为 "原查询 [SEP] 生成的法律文档片段"
        """
        if not self.enabled:
            logger.debug("Query2doc增强已禁用，返回原查询")
            return user_query

        if not user_query or not user_query.strip():
            logger.warning("用户查询为空，无法进行Query2doc增强")
            return user_query

        try:
            logger.debug(f"开始Query2doc增强: '{user_query}'")

            # 构建提示词
            prompt = self.prompt_template.format(query=user_query.strip())

            # 调用LLM生成假设文档片段
            pseudo_document = await self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            if pseudo_document and pseudo_document.strip():
                # 清理生成的内容
                cleaned_pseudo_doc = self._clean_generated_content(pseudo_document)

                if cleaned_pseudo_doc:
                    # 组合原查询和生成的文档片段
                    enhanced_query = f"{user_query} [SEP] {cleaned_pseudo_doc}"

                    logger.info(f"Query2doc增强成功: '{user_query}' -> '{cleaned_pseudo_doc[:50]}...'")
                    logger.debug(f"完整增强结果: {enhanced_query}")

                    return enhanced_query
                else:
                    logger.warning("生成的文档片段清理后为空，使用原查询")
                    return user_query
            else:
                logger.warning("LLM未生成有效内容，使用原查询")
                return user_query

        except Exception as e:
            logger.error(f"Query2doc增强失败: {e}")
            # 降级处理：返回原查询
            return user_query

    def _clean_generated_content(self, content: str) -> str:
        """
        清理LLM生成的内容

        Args:
            content: LLM生成的原始内容

        Returns:
            清理后的内容
        """
        if not content:
            return ""

        # 基础清理
        cleaned = content.strip()

        # 移除常见的无用前缀
        prefixes_to_remove = [
            "生成的法律文档片段：",
            "法律文档片段：",
            "文档片段：",
            "回答：",
            "答：",
        ]

        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break

        # 移除引号
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()
        if cleaned.startswith('「') and cleaned.endswith('」'):
            cleaned = cleaned[1:-1].strip()

        # 长度限制和质量检查
        if len(cleaned) < 10:
            logger.warning(f"生成内容过短: '{cleaned}'")
            return ""

        if len(cleaned) > 200:
            logger.debug(f"生成内容过长，截取前200字符")
            cleaned = cleaned[:200] + "..."

        # 简单质量检查：确保包含法律相关内容
        legal_keywords = ["法", "罪", "条", "律", "刑", "判", "责任", "处罚", "违法", "犯罪"]
        if not any(keyword in cleaned for keyword in legal_keywords):
            logger.warning(f"生成内容缺乏法律相关性: '{cleaned}'")
            # 仍然返回内容，因为可能有其他有用信息

        return cleaned

    def get_enhancement_stats(self) -> dict:
        """
        获取增强器统计信息

        Returns:
            包含统计信息的字典
        """
        return {
            "enabled": self.enabled,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "prompt_template_length": len(self.prompt_template),
        }

    def update_config(self, **kwargs):
        """
        动态更新配置参数

        Args:
            **kwargs: 要更新的配置参数
        """
        if 'max_tokens' in kwargs:
            self.max_tokens = kwargs['max_tokens']
            logger.info(f"Query2doc max_tokens更新为: {self.max_tokens}")

        if 'temperature' in kwargs:
            self.temperature = kwargs['temperature']
            logger.info(f"Query2doc temperature更新为: {self.temperature}")

        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
            logger.info(f"Query2doc启用状态更新为: {self.enabled}")