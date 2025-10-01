#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HyDE (Hypothetical Document Embeddings) 增强器
通过LLM生成假设性法律专业回答，然后用这个回答进行向量搜索
"""

import logging
from typing import Optional
from src.infrastructure.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)

class HyDEEnhancer:
    """HyDE答案导向增强器

    核心思想：生成一个假设性的专业法律回答，然后用这个回答去搜索
    相似的真实文档，这样能找到在表达方式和专业度上更匹配的内容。
    """

    def __init__(self, llm_client: LLMClient, config):
        """
        初始化HyDE增强器

        Args:
            llm_client: LLM客户端实例
            config: 配置对象，包含提示词模板和参数
        """
        self.llm_client = llm_client
        self.config = config

        # 从配置获取提示词模板和参数
        self.prompt_template = config.HYDE_PROMPT_TEMPLATE
        self.max_tokens = config.HYDE_MAX_TOKENS
        self.temperature = config.HYDE_TEMPERATURE
        self.enabled = config.ENABLE_HYDE

        logger.info(f"HyDE增强器初始化完成，启用状态: {self.enabled}")

    async def generate_hypothetical_answer(self, user_query: str) -> str:
        """
        生成假设性法律专业回答

        Args:
            user_query: 用户原始问题

        Returns:
            生成的假设性专业回答，如果生成失败则返回原查询
        """
        if not self.enabled:
            logger.debug("HyDE增强已禁用，返回原查询")
            return user_query

        if not user_query or not user_query.strip():
            logger.warning("用户查询为空，无法进行HyDE增强")
            return user_query

        try:
            logger.debug(f"开始HyDE增强: '{user_query}'")

            # 构建提示词
            prompt = self.prompt_template.format(query=user_query.strip())

            # 调用LLM生成假设性回答
            hypothetical_answer = await self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            if hypothetical_answer and hypothetical_answer.strip():
                # 清理生成的回答
                cleaned_answer = self._clean_generated_answer(hypothetical_answer)

                if cleaned_answer:
                    logger.info(f"HyDE增强成功: '{user_query}' -> '{cleaned_answer[:50]}...'")
                    logger.debug(f"完整HyDE回答: {cleaned_answer}")
                    return cleaned_answer
                else:
                    logger.warning("生成的回答清理后为空，使用原查询")
                    return user_query
            else:
                logger.warning("LLM未生成有效回答，使用原查询")
                return user_query

        except Exception as e:
            logger.error(f"HyDE增强失败: {e}")
            # 降级处理：返回原查询
            return user_query

    def _clean_generated_answer(self, answer: str) -> str:
        """
        清理LLM生成的回答

        Args:
            answer: LLM生成的原始回答

        Returns:
            清理后的回答
        """
        if not answer:
            return ""

        # 基础清理
        cleaned = answer.strip()

        # 移除常见的无用前缀和后缀
        prefixes_to_remove = [
            "专业回答：",
            "回答：",
            "答：",
            "法律回答：",
            "根据相关法律规定：",
            "依据法律规定：",
        ]

        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break

        # 移除常见的结束语
        suffixes_to_remove = [
            "具体情况请咨询专业律师。",
            "建议咨询专业律师。",
            "请咨询专业法律人士。",
            "以上仅供参考。",
            "详情请咨询法律专家。",
        ]

        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        # 移除引号
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()
        if cleaned.startswith('「') and cleaned.endswith('」'):
            cleaned = cleaned[1:-1].strip()

        # 长度限制和质量检查
        if len(cleaned) < 15:
            logger.warning(f"生成回答过短: '{cleaned}'")
            return ""

        if len(cleaned) > 300:
            logger.debug(f"生成回答过长，截取前300字符")
            # 尝试在句号处截断
            sentences = cleaned[:300].split('。')
            if len(sentences) > 1:
                cleaned = '。'.join(sentences[:-1]) + '。'
            else:
                cleaned = cleaned[:300] + "..."

        # 质量检查：确保回答具有法律专业性
        professional_indicators = [
            "根据", "依据", "法", "条", "律", "规定", "罪", "刑", "处", "判", "责任", "违法",
            "构成", "情节", "量刑", "处罚", "案例", "司法解释", "最高法", "刑法"
        ]

        if not any(indicator in cleaned for indicator in professional_indicators):
            logger.warning(f"生成回答缺乏法律专业性: '{cleaned[:30]}...'")
            # 仍然返回内容，但会记录警告

        # 移除过于口语化的表达
        colloquial_patterns = [
            "你好", "您好", "请问", "谢谢", "不客气", "希望对您有帮助"
        ]

        for pattern in colloquial_patterns:
            cleaned = cleaned.replace(pattern, "").strip()

        return cleaned

    def _validate_answer_quality(self, answer: str) -> bool:
        """
        验证生成回答的质量

        Args:
            answer: 生成的回答

        Returns:
            是否通过质量检查
        """
        if not answer or len(answer) < 15:
            return False

        # 检查是否包含法律相关内容
        legal_keywords = ["法", "罪", "条", "律", "刑", "判", "责任", "处罚", "违法", "犯罪"]
        has_legal_content = any(keyword in answer for keyword in legal_keywords)

        # 检查是否过于口语化
        colloquial_markers = ["怎么办", "咋办", "啥", "咋", "嘛", "呢", "吧"]
        too_colloquial = sum(1 for marker in colloquial_markers if marker in answer) > 2

        return has_legal_content and not too_colloquial

    async def enhance_query_with_context(self, user_query: str, context_info: dict = None) -> str:
        """
        基于上下文信息增强查询

        Args:
            user_query: 用户查询
            context_info: 可选的上下文信息（如之前的搜索结果）

        Returns:
            增强后的查询
        """
        if context_info and context_info.get('previous_results'):
            # 如果有之前的搜索结果，可以利用这些信息生成更精确的假设回答
            context_prompt = f"\n\n参考信息：{context_info.get('summary', '')}"
            enhanced_template = self.prompt_template + context_prompt

            prompt = enhanced_template.format(query=user_query.strip())
        else:
            prompt = self.prompt_template.format(query=user_query.strip())

        try:
            return await self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
        except Exception as e:
            logger.error(f"上下文增强失败: {e}")
            return await self.generate_hypothetical_answer(user_query)

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
            logger.info(f"HyDE max_tokens更新为: {self.max_tokens}")

        if 'temperature' in kwargs:
            self.temperature = kwargs['temperature']
            logger.info(f"HyDE temperature更新为: {self.temperature}")

        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
            logger.info(f"HyDE启用状态更新为: {self.enabled}")