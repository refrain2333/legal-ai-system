#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的LLM客户端，支持Gemini多模型备选机制 + GLM备用
当主要模型失败时自动尝试其他Gemini模型，最后才切换到GLM
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI, APIError

logger = logging.getLogger(__name__)


import os
import asyncio
import logging
import httpx
import json
import random
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI, APIError

logger = logging.getLogger(__name__)

class LLMClient:
    """支持Cloudflare, GLM, Gemini, SiliconFlow四服务,并按顺序备选的LLM客户端"""

    def __init__(self, config):
        self.config = config

        # 检查LLM总开关
        self.llm_enabled = getattr(config, 'LLM_ENABLED', True)
        if not self.llm_enabled:
            logger.info("LLM功能已禁用，跳过所有LLM服务初始化")
            self.cf_client = None
            self.glm_client = None
            self.gemini_client = None
            self.siliconflow_client = None
            return

        # 读取各服务商开关
        self.cf_enabled = getattr(config, 'LLM_PROVIDER_CLOUDFLARE', True)
        self.glm_enabled = getattr(config, 'LLM_PROVIDER_GLM', False)
        self.gemini_enabled = getattr(config, 'LLM_PROVIDER_GEMINI', False)
        self.siliconflow_enabled = getattr(config, 'LLM_PROVIDER_SILICONFLOW', False)

        # Cloudflare 配置 (主服务)
        self.cf_config = {
            'account_id': getattr(config, 'CF_ACCOUNT_ID', None),
            'api_token': getattr(config, 'CF_API_TOKEN', None),
            'model': getattr(config, 'CF_MODEL', '@cf/openai/gpt-oss-20b')
        }

        # GLM配置 (备选1)
        self.glm_config = {
            'api_key': getattr(config, 'GLM_API_KEY', None),
            'base_url': getattr(config, 'GLM_API_BASE', None),
            'model': getattr(config, 'GLM_MODEL', 'glm-4.5-flash')
        }

        # Gemini配置 (备选2)
        self.gemini_config = {
            'api_key': getattr(config, 'GEMINI_API_KEY', None),
            'base_url': getattr(config, 'GEMINI_API_BASE', None),
            'models': getattr(config, 'GEMINI_MODELS', ["gemini-2.5-flash-lite"])
        }

        # 硅基流动配置 (备选3)
        self.siliconflow_config = {
            'api_key': getattr(config, 'SILICONFLOW_API_KEY', None),
            'base_url': getattr(config, 'SILICONFLOW_API_BASE', None),
            'models': getattr(config, 'SILICONFLOW_MODELS', [
                "Qwen/Qwen2.5-7B-Instruct",
                "deepseek-ai/DeepSeek-V2.5",
                "meta-llama/Meta-Llama-3.1-8B-Instruct"
            ])
        }

        # 通用配置
        self.timeout = getattr(config, 'LLM_REQUEST_TIMEOUT', 120) # 增加超时到120秒
        self.max_retries = getattr(config, 'LLM_MAX_RETRIES', 2) # 增加重试次数
        self.enable_fallback = getattr(config, 'LLM_ENABLE_FALLBACK', True)

        # 只初始化启用的客户端
        self.cf_client = None
        self.glm_client = None
        self.gemini_client = None
        self.siliconflow_client = None

        if self.cf_enabled and self.cf_config['account_id'] and self.cf_config['api_token']:
            # 不在这里创建httpx客户端，改为每次请求时创建新的
            self.cf_client = True  # 标记为已启用
            logger.info(f"Cloudflare服务已启用，将按需创建httpx客户端")
        else:
            self.cf_client = None
            logger.warning(f"Cloudflare配置不完整，跳过客户端创建")

        if self.glm_enabled:
            self.glm_client = self._create_openai_client(self.glm_config, "GLM")

        if self.gemini_enabled:
            self.gemini_client = self._create_openai_client(self.gemini_config, "Gemini")

        if self.siliconflow_enabled:
            self.siliconflow_client = self._create_openai_client(self.siliconflow_config, "SiliconFlow")

        # 当前状态
        self.current_service = "siliconflow"  # 默认使用硅基流动作为主服务
        self.failed_models = set()

        logger.info(f"LLM客户端初始化完成")
        logger.info(f"  - LLM总开关: {self.llm_enabled}")
        logger.info(f"  - Cloudflare开关: {self.cf_enabled}, 可用: {self.cf_client is not None}")
        logger.info(f"  - GLM开关: {self.glm_enabled}, 可用: {self.glm_client is not None}")
        logger.info(f"  - Gemini开关: {self.gemini_enabled}, 可用: {self.gemini_client is not None}")
        logger.info(f"  - SiliconFlow开关: {self.siliconflow_enabled}, 可用: {self.siliconflow_client is not None}")
        logger.info(f"  - 启用备选: {self.enable_fallback}")

    def _create_openai_client(self, config: Dict[str, Any], service_name: str) -> Optional[AsyncOpenAI]:
        api_key = config.get('api_key')
        base_url = config.get('base_url')
        if not api_key or not base_url:
            logger.warning(f"{service_name} 配置不完整，跳过初始化")
            return None
        try:
            return AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=float(self.timeout), max_retries=self.max_retries)
        except Exception as e:
            logger.error(f"{service_name} 客户端初始化失败: {e}")
            return None

    async def generate_text(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.2) -> str:
        if not self.llm_enabled:
            logger.warning("LLM功能已禁用，返回空结果")
            return ""
        return await self._try_with_fallback(prompt, max_tokens, temperature)

    async def _try_with_fallback(self, prompt: str, max_tokens: int, temperature: float) -> str:
        # 1. 优先尝试 SiliconFlow (如果启用)
        if self.siliconflow_enabled and self.siliconflow_client and self.siliconflow_config['models']:
            logger.info("🚀 使用SiliconFlow主服务")

            # 对每个模型进行多次重试（指数退避）
            for model in self.siliconflow_config['models']:
                if model in self.failed_models:
                    continue

                # 对每个模型进行最多2次重试
                for attempt in range(self.max_retries + 1):
                    try:
                        result = await self._generate_with_openai_client(self.siliconflow_client, prompt, model, max_tokens, temperature, f"SiliconFlow({model})")
                        if result:
                            self.current_service = "siliconflow"
                            logger.info(f"✅ 使用SiliconFlow主服务成功: {model}")
                            return result
                    except Exception as e:
                        error_type = type(e).__name__
                        if "APITimeoutError" in error_type or "Timeout" in error_type:
                            if attempt < self.max_retries:
                                # 指数退避：1秒，2秒
                                wait_time = (2 ** attempt)
                                logger.warning(f"SiliconFlow主服务模型 {model} 超时，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.warning(f"SiliconFlow主服务模型 {model} 超时重试耗尽: {e}")
                                self.failed_models.add(model)
                        else:
                            logger.warning(f"SiliconFlow主服务模型 {model} 失败: {e}")
                            self.failed_models.add(model)
                        break

        # 2. 如果SiliconFlow失败，尝试 Cloudflare (如果启用)
        if self.enable_fallback and self.cf_enabled and self.cf_client:
            logger.info("🔄 切换到Cloudflare备选服务")
            try:
                result = await self._generate_with_cloudflare(prompt, max_tokens, temperature)
                if result:
                    self.current_service = "cloudflare"
                    logger.info(f"✅ 使用Cloudflare备选服务成功")
                    return result
            except Exception as e:
                logger.error(f"Cloudflare备选服务失败: {e}")

        # 3. 如果Cloudflare也失败，尝试 GLM (如果启用)
        if self.enable_fallback and self.glm_enabled and self.glm_client:
            logger.info("🔄 切换到GLM备选服务")
            try:
                result = await self._generate_with_openai_client(self.glm_client, prompt, self.glm_config['model'], max_tokens, temperature, "GLM")
                if result:
                    self.current_service = "glm"
                    return result
            except Exception as e:
                logger.error(f"GLM备选服务失败: {e}")

        # 4. 如果GLM也失败，尝试 Gemini (如果启用)
        if self.enable_fallback and self.gemini_enabled and self.gemini_client and self.gemini_config['models']:
            logger.info("🔄 切换到Gemini备选服务")
            for model in self.gemini_config['models']:
                if model in self.failed_models:
                    continue
                try:
                    result = await self._generate_with_openai_client(self.gemini_client, prompt, model, max_tokens, temperature, f"Gemini({model})")
                    if result:
                        self.current_service = "gemini"
                        return result
                except Exception as e:
                    logger.warning(f"Gemini备选模型 {model} 失败: {e}")
                    self.failed_models.add(model)
                    continue

        logger.error("🚫 所有启用的LLM服务和模型都不可用")
        return ""

    async def _generate_with_cloudflare(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_config['account_id']}/ai/run/{self.cf_config['model']}"
        headers = {
            "Authorization": f"Bearer {self.cf_config['api_token']}",
            "Content-Type": "application/json"
        }
        data = {"input": prompt}

        # 🚀 性能优化：大幅减少重试次数和超时时间
        max_retries = 0  # 不重试，快速失败
        
        for attempt in range(max_retries + 1):  # 最多执行1次
            try:
                # 🚀 极限性能优化：超短超时，快速失败
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(65.0, connect=5.0, read=60.0),  # 延长超时以处理慢响应
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),  # 启用连接重用
                    follow_redirects=True
                ) as client:
                    logger.info(f"🤖 向 Cloudflare AI 发送请求 (尝试 {attempt + 1}/{max_retries + 1})")
                    
                    response = await client.post(url, headers=headers, json=data)
                    response.raise_for_status()

                    result_json = response.json()

                    # 快速解析响应
                    if result_json.get('success') and result_json.get('result'):
                        output = result_json['result'].get('output', [])
                        if isinstance(output, list) and len(output) > 0:
                            # 通常最后一个message是助手的回答
                            assistant_message = output[-1]
                            if assistant_message.get('role') == 'assistant' and assistant_message.get('content'):
                                content_list = assistant_message['content']
                                if isinstance(content_list, list) and len(content_list) > 0 and content_list[0].get('type') == 'output_text':
                                    generated_text = content_list[0].get('text', '').strip()
                                    if generated_text:
                                        # 简化Unicode清理
                                        cleaned_text = generated_text.replace('\u202f', ' ').replace('\u2009', ' ').replace('\u200b', '')
                                        logger.debug(f"✅ Cloudflare AI成功返回内容，长度: {len(cleaned_text)}")
                                        return cleaned_text

                    logger.warning(f"⚠️ Cloudflare AI返回了非预期的格式或空内容")
                    return None
                    
            except httpx.RemoteProtocolError as e:
                if attempt == max_retries:
                    logger.error(f"❌ Cloudflare连接失败，已重试{max_retries}次: {e}")
                    raise e
                logger.warning(f"🔄 Cloudflare连接协议错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                await asyncio.sleep(0.5)  # 快速重试
                continue
                
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.TimeoutException) as e:
                # 快速失败，不重试
                logger.warning(f"🔄 Cloudflare网络错误，快速失败: {type(e).__name__}")
                raise e
                
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ Cloudflare AI HTTP状态错误: {e.response.status_code}")
                # 对于4xx错误，不重试
                if 400 <= e.response.status_code < 500:
                    raise e
                # 对于5xx错误，重试
                if attempt == max_retries:
                    raise e
                await asyncio.sleep(0.5)
                continue
                
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"❌ Cloudflare AI调用失败，已重试{max_retries}次: {type(e).__name__}: {str(e)}")
                    raise e
                logger.warning(f"🔄 Cloudflare AI其他错误 (尝试 {attempt + 1}/{max_retries + 1}): {type(e).__name__}")
                await asyncio.sleep(0.5)
                continue

        logger.error(f"❌ Cloudflare AI调用失败，已达到最大重试次数({max_retries})")
        return None

    async def _generate_with_openai_client(self, client: AsyncOpenAI, prompt: str, model: str, max_tokens: int, temperature: float, service_name: str) -> Optional[str]:
        messages = [{"role": "user", "content": prompt}]

        # 为不同服务添加专门的系统提示词
        if "Gemini" in service_name:
            messages.insert(0, {"role": "system", "content": "你是一个专业的法律AI助手，请用准确的法律术语回答问题。"})
        elif "SiliconFlow" in service_name:
            messages.insert(0, {"role": "system", "content": "你是一个专业的刑事法律AI助手，精通中华人民共和国刑法。请用准确的法律术语回答问题，重点关注刑事法律领域的法条、案例和司法解释。"})

        try:
            logger.debug(f"🤖 使用{service_name}生成文本: '{prompt[:50]}...'")
            response = await client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
            if response.choices and response.choices[0].message:
                generated_text = response.choices[0].message.content
                if generated_text:
                    cleaned_text = self._clean_unicode_for_windows(generated_text.strip())
                    return cleaned_text
            logger.warning(f"⚠️ {service_name}返回了空内容或无效结构")
            return None
        except APIError as e:
            status_code = getattr(e, 'status_code', 'N/A')
            message = getattr(e, 'message', str(e))
            logger.error(f"❌ {service_name} API错误: {status_code} - {message}")
            raise e
        except Exception as e:
            logger.error(f"❌ {service_name}调用失败: {e}")
            raise e

    def get_current_service(self) -> str:
        """获取当前使用的模型名称（仅模型，不显示渠道）"""
        if self.current_service == "cloudflare":
            return self.cf_config['model']  # 只返回模型名称
        elif self.current_service == "glm":
            return self.glm_config['model']
        elif self.current_service == "gemini":
            # 获取当前使用的Gemini模型
            current_model = self.gemini_config['models'][0] if self.gemini_config['models'] else "gemini-2.5-flash-lite"
            return current_model
        elif self.current_service == "siliconflow":
            # 获取当前使用的SiliconFlow模型
            current_model = self.siliconflow_config['models'][0] if self.siliconflow_config['models'] else "Qwen/Qwen3-Next-80B-A3B-Instruct"
            return current_model
        else:
            return self.current_service

    def get_current_model_name(self) -> str:
        """获取当前模型的具体名称"""
        return self.get_current_service()  # 与get_current_service保持一致

    def get_current_provider(self) -> str:
        """获取当前服务提供商"""
        return self.current_service

    async def close(self):
        """关闭所有客户端连接"""
        # 现在cf_client是按需创建的，不需要手动关闭
        pass

    def __del__(self):
        """析构函数"""
        # 现在不需要手动清理httpx客户端
        pass

    def _clean_unicode_for_windows(self, text: str) -> str:
        """清理可能在Windows GBK编码下导致问题的Unicode字符"""
        if not text:
            return text

        # 替换常见的problematic Unicode字符
        problematic_chars = {
            '\u202f': ' ',  # Narrow no-break space -> regular space
            '\u2009': ' ',  # Thin space -> regular space
            '\u200b': '',   # Zero-width space -> remove
            '\u2060': '',   # Word joiner -> remove
            '\ufeff': '',   # Byte order mark -> remove
            '\u00a0': ' ',  # Non-breaking space -> regular space
        }

        cleaned_text = text
        for problematic, replacement in problematic_chars.items():
            cleaned_text = cleaned_text.replace(problematic, replacement)

        # 过滤掉其他可能问题的控制字符
        cleaned_text = ''.join(char for char in cleaned_text if ord(char) < 65536 and (ord(char) < 32 and ord(char) in [9, 10, 13]) or ord(char) >= 32)

        return cleaned_text
