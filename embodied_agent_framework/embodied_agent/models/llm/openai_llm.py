"""
OpenAI LLM Implementation - OpenAI兼容的大语言模型实现
支持OpenAI官方API以及兼容OpenAI格式的其他LLM服务
"""

import asyncio
import time
import os
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available, OpenAILLM will not work")
    OPENAI_AVAILABLE = False

from ...interfaces.llm import LLMInterface, ChatMessage, LLMResponse, MessageRole


class OpenAILLM(LLMInterface):
    """
    OpenAI兼容的大语言模型实现
    支持OpenAI官方API以及兼容OpenAI格式的其他LLM服务
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI LLM

        Args:
            config: 配置参数，包含:
                - api_key: API密钥
                - base_url: 服务地址（可选，默认为OpenAI官方地址）
                - model_name: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大token数
        """
        super().__init__(config)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required for OpenAILLM")

        # 从环境变量或配置中获取参数
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.base_url = config.get('base_url') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model_name = config.get('model_name') or os.getenv('OPENAI_MODEL_NAME', 'gpt-4')

        if not self.api_key:
            raise ValueError("Missing required configuration: api_key")

        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"OpenAILLM initialized with model: {self.model_name} at {self.base_url}")

    async def generate_response(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        """
        生成响应

        Args:
            messages: 对话消息列表
            **kwargs: 额外参数

        Returns:
            LLMResponse: 生成的响应
        """
        start_time = time.time()

        try:
            # 准备消息格式
            api_messages = self.prepare_messages(messages)

            # 生成参数
            generation_params = {
                'model': self.model_name,
                'messages': api_messages,
                'temperature': kwargs.get('temperature', self.temperature),
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            }

            # 添加top_p参数（如果支持）
            if 'top_p' in kwargs:
                generation_params['top_p'] = kwargs['top_p']
            elif hasattr(self, 'top_p'):
                generation_params['top_p'] = self.top_p

            # 调用API
            response = await self._call_api_with_retry(generation_params)

            # 解析响应
            content = response.choices[0].message.content.strip()
            tokens_used = getattr(response.usage, 'total_tokens', None) if hasattr(response, 'usage') else None

            latency = time.time() - start_time

            return LLMResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                latency=latency
            )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def generate_single(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        生成单个响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            LLMResponse: 生成的响应
        """
        messages = []

        # 添加系统提示
        if system_prompt:
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))

        # 添加用户提示
        messages.append(ChatMessage(role=MessageRole.USER, content=prompt))

        return await self.generate_response(messages, **kwargs)

    async def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            bool: 连接是否成功
        """
        try:
            test_response = await self.generate_single(
                "Hello, please reply 'connection ok' to confirm the connection is working.",
                **{'max_tokens': 50, 'temperature': 0.1}
            )
            success = "ok" in test_response.content.lower() or "connection" in test_response.content.lower()
            if success:
                logger.info("OpenAILLM connection test successful")
            else:
                logger.warning(f"OpenAILLM connection test questionable: {test_response.content}")
            return success

        except Exception as e:
            logger.error(f"OpenAILLM connection test failed: {e}")
            return False

    async def _call_api_with_retry(self, params: Dict[str, Any]) -> Any:
        """
        带重试的API调用

        Args:
            params: API调用参数

        Returns:
            Any: API响应

        Raises:
            Exception: 重试失败后抛出最后一个异常
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # 由于OpenAI客户端是同步的，我们在线程池中运行它
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(**params)
                )
                return response

            except Exception as e:
                last_exception = e
                logger.warning(f"API call attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    # 指数退避
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

        # 所有重试都失败了
        logger.error(f"All {self.max_retries} API call attempts failed")
        raise last_exception

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        info = super().get_model_info()
        info.update({
            'provider': 'openai',
            'api_available': OPENAI_AVAILABLE,
            'client_initialized': hasattr(self, 'client'),
            'available_models': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini'],
        })
        return info