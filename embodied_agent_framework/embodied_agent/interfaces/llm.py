"""
Large Language Model Interface - Abstract base class for LLM integrations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel
import time


class MessageRole(Enum):
    """Message roles for chat conversations"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Chat message data structure"""
    role: MessageRole
    content: str
    timestamp: Optional[float] = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        super().__init__(**data)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API calls"""
        return {
            "role": self.role.value,
            "content": self.content
        }


class LLMResponse(BaseModel):
    """LLM response data structure"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    latency: Optional[float] = None
    timestamp: float = time.time()


class LLMInterface(ABC):
    """
    Abstract base class for Large Language Model interfaces.

    This interface provides a standardized way to interact with different
    LLM providers while abstracting away vendor-specific details.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM interface

        Args:
            config: LLM-specific configuration parameters
        """
        self.config = config
        self.model_name = config.get('model_name', 'unknown')
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')

        # Generation parameters
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        self.top_p = config.get('top_p', 0.9)

        # Request settings
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)

    @abstractmethod
    async def generate_response(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        """
        Generate response from chat messages

        Args:
            messages: List of chat messages
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Generated response
        """
        pass

    @abstractmethod
    async def generate_single(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        Generate response from single prompt

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Generated response
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to LLM service

        Returns:
            bool: True if connection successful
        """
        pass

    def prepare_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """
        Prepare messages for API call

        Args:
            messages: List of ChatMessage objects

        Returns:
            List[Dict[str, str]]: Messages in API format
        """
        return [msg.to_dict() for msg in messages]

    def create_chat_message(self, role: Union[str, MessageRole], content: str) -> ChatMessage:
        """
        Create a chat message

        Args:
            role: Message role (string or MessageRole enum)
            content: Message content

        Returns:
            ChatMessage: Created message
        """
        if isinstance(role, str):
            role = MessageRole(role)
        return ChatMessage(role=role, content=content)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information

        Returns:
            Dict[str, Any]: Model information
        """
        return {
            'model_name': self.model_name,
            'base_url': self.base_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p
        }