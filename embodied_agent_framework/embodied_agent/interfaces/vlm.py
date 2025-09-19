"""
Vision Language Model Interface - Abstract base class for VLM integrations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from pydantic import BaseModel
import time
import base64
from PIL import Image
import numpy as np


class VLMTaskType(Enum):
    """VLM task types"""
    OBJECT_DETECTION = "object_detection"
    VISUAL_QUESTION_ANSWERING = "visual_question_answering"
    IMAGE_DESCRIPTION = "image_description"
    GROUNDING = "grounding"


class BoundingBox(BaseModel):
    """Bounding box for object detection"""
    x1: int
    y1: int
    x2: int
    y2: int
    label: str
    confidence: float = 1.0


class VLMResponse(BaseModel):
    """VLM response data structure"""
    content: str
    task_type: VLMTaskType
    model: str
    bounding_boxes: Optional[List[BoundingBox]] = None
    confidence: Optional[float] = None
    latency: Optional[float] = None
    timestamp: float = time.time()


class VLMInterface(ABC):
    """
    Abstract base class for Vision Language Model interfaces.

    This interface provides a standardized way to interact with different
    VLM providers while abstracting away vendor-specific details.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize VLM interface

        Args:
            config: VLM-specific configuration parameters
        """
        self.config = config
        self.model_name = config.get('model_name', 'unknown')
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')

        # Generation parameters
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

        # Request settings
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)

    @abstractmethod
    async def process_image(self, image_path: str, prompt: str,
                          task_type: VLMTaskType = VLMTaskType.VISUAL_QUESTION_ANSWERING,
                          **kwargs) -> VLMResponse:
        """
        Process image with text prompt

        Args:
            image_path: Path to image file
            prompt: Text prompt describing the task
            task_type: Type of VLM task to perform
            **kwargs: Additional parameters

        Returns:
            VLMResponse: Model response
        """
        pass

    @abstractmethod
    async def detect_objects(self, image_path: str, prompt: str, **kwargs) -> VLMResponse:
        """
        Detect and ground objects in image

        Args:
            image_path: Path to image file
            prompt: Object detection prompt
            **kwargs: Additional parameters

        Returns:
            VLMResponse: Detection results with bounding boxes
        """
        pass

    @abstractmethod
    async def answer_visual_question(self, image_path: str, question: str, **kwargs) -> VLMResponse:
        """
        Answer question about image

        Args:
            image_path: Path to image file
            question: Question about the image
            **kwargs: Additional parameters

        Returns:
            VLMResponse: Answer to the question
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to VLM service

        Returns:
            bool: True if connection successful
        """
        pass

    def encode_image_base64(self, image_path: str) -> str:
        """
        Encode image to base64 string

        Args:
            image_path: Path to image file

        Returns:
            str: Base64 encoded image with data URL prefix
        """
        try:
            with open(image_path, 'rb') as image_file:
                encoded = base64.b64encode(image_file.read()).decode('utf-8')
                return f'data:image/jpeg;base64,{encoded}'
        except Exception as e:
            raise ValueError(f"Failed to encode image: {e}")

    def validate_image(self, image_path: str) -> bool:
        """
        Validate image file

        Args:
            image_path: Path to image file

        Returns:
            bool: True if image is valid
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get image information

        Args:
            image_path: Path to image file

        Returns:
            Dict[str, Any]: Image information
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': len(open(image_path, 'rb').read())
                }
        except Exception as e:
            return {'error': str(e)}

    def parse_grounding_response(self, response_text: str) -> List[BoundingBox]:
        """
        Parse grounding response to extract bounding boxes

        Args:
            response_text: Raw response text from VLM

        Returns:
            List[BoundingBox]: Parsed bounding boxes
        """
        # This is a base implementation that should be overridden by specific VLM implementations
        # Different VLMs may have different response formats
        return []

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
            'supports_grounding': hasattr(self, 'detect_objects'),
            'supports_vqa': hasattr(self, 'answer_visual_question')
        }