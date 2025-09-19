"""
OpenAI VLM Implementation - OpenAI兼容的视觉语言模型实现
支持OpenAI官方API以及兼容OpenAI格式的其他多模态模型服务
"""

import asyncio
import time
import os
import json
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available, OpenAIVLM will not work")
    OPENAI_AVAILABLE = False

from ...interfaces.vlm import VLMInterface, VLMResponse, VLMTaskType, BoundingBox


class OpenAIVLM(VLMInterface):
    """
    OpenAI兼容的视觉语言模型实现
    支持OpenAI官方API以及兼容OpenAI格式的其他多模态模型服务
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI VLM

        Args:
            config: 配置参数
        """
        super().__init__(config)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required for OpenAIVLM")

        # 配置参数
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.base_url = config.get('base_url') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model_name = config.get('model_name') or os.getenv('OPENAI_VLM_MODEL', 'gpt-4o')

        if not self.api_key:
            raise ValueError("Missing required configuration: api_key")

        # 系统提示词
        self.grounding_prompt = """
I will give you an instruction for a robotic arm. Please extract the start object and end object from the instruction, and find the pixel coordinates of these two objects in the image (top-left and bottom-right corners). Output in JSON format.

For example, if my instruction is: "Please help me put the red cube on the house drawing."
You should output this format:
{
 "start":"red cube",
 "start_xyxy":[[102,505],[324,860]],
 "end":"house drawing",
 "end_xyxy":[[300,150],[476,310]]
}

Only reply with the JSON itself, no other content.

My current instruction is:
"""

        self.vqa_prompt = """
Please describe what you see in this image. Tell me about each object's name, category, and function. Describe each object in one sentence.

For example:
Lianhua Qingwen Capsule, medicine, treats colds.
Plate, household item, holds things.
Loratadine Tablet, medicine, treats allergies.

My current question is:
"""

        # 创建客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"OpenAIVLM initialized with model: {self.model_name} at {self.base_url}")

    async def process_image(self, image_path: str, prompt: str,
                          task_type: VLMTaskType = VLMTaskType.VISUAL_QUESTION_ANSWERING,
                          **kwargs) -> VLMResponse:
        """
        处理图像和文本提示

        Args:
            image_path: 图像文件路径
            prompt: 文本提示
            task_type: 任务类型
            **kwargs: 额外参数

        Returns:
            VLMResponse: 模型响应
        """
        start_time = time.time()

        try:
            # 验证图像
            if not self.validate_image(image_path):
                raise ValueError(f"Invalid image file: {image_path}")

            # 编码图像
            image_data = self.encode_image_base64(image_path)

            # 构建系统提示
            if task_type == VLMTaskType.OBJECT_DETECTION:
                system_prompt = self.grounding_prompt + prompt
            else:
                system_prompt = self.vqa_prompt + prompt

            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": system_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ]

            # API参数
            params = {
                'model': self.model_name,
                'messages': messages,
                'temperature': kwargs.get('temperature', self.temperature),
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            }

            # 调用API
            response = await self._call_api_with_retry(params)

            content = response.choices[0].message.content.strip()
            latency = time.time() - start_time

            # 解析响应
            bounding_boxes = None
            confidence = None

            if task_type == VLMTaskType.OBJECT_DETECTION:
                bounding_boxes, confidence = self._parse_grounding_response(content)

            return VLMResponse(
                content=content,
                task_type=task_type,
                model=self.model_name,
                bounding_boxes=bounding_boxes,
                confidence=confidence,
                latency=latency
            )

        except Exception as e:
            logger.error(f"OpenAIVLM processing error: {e}")
            raise

    async def detect_objects(self, image_path: str, prompt: str, **kwargs) -> VLMResponse:
        """检测和定位物体"""
        return await self.process_image(
            image_path, prompt, VLMTaskType.OBJECT_DETECTION, **kwargs
        )

    async def answer_visual_question(self, image_path: str, question: str, **kwargs) -> VLMResponse:
        """回答视觉问题"""
        return await self.process_image(
            image_path, question, VLMTaskType.VISUAL_QUESTION_ANSWERING, **kwargs
        )

    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            # 创建一个简单的测试图像
            test_image_path = 'temp/test_connection.jpg'
            self._create_test_image(test_image_path)

            response = await self.answer_visual_question(
                test_image_path,
                "What do you see in this image?"
            )

            success = len(response.content) > 10
            if success:
                logger.info("OpenAIVLM connection test successful")
            return success

        except Exception as e:
            logger.error(f"OpenAIVLM connection test failed: {e}")
            return False

    async def _call_api_with_retry(self, params: Dict[str, Any]) -> Any:
        """带重试的API调用"""
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(**params)
                )
                return response

            except Exception as e:
                last_exception = e
                logger.warning(f"OpenAIVLM API call attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

        logger.error(f"All {self.max_retries} OpenAIVLM API call attempts failed")
        raise last_exception

    def _parse_grounding_response(self, response_text: str) -> tuple[Optional[List[BoundingBox]], Optional[float]]:
        """
        解析定位响应

        Args:
            response_text: 模型响应文本

        Returns:
            tuple: (边界框列表, 置信度)
        """
        try:
            # 尝试解析JSON响应
            data = json.loads(response_text)

            bboxes = []

            # 解析起始物体
            if 'start' in data and 'start_xyxy' in data:
                start_coords = data['start_xyxy']
                if len(start_coords) == 2 and len(start_coords[0]) == 2 and len(start_coords[1]) == 2:
                    bbox = BoundingBox(
                        x1=int(start_coords[0][0]),
                        y1=int(start_coords[0][1]),
                        x2=int(start_coords[1][0]),
                        y2=int(start_coords[1][1]),
                        label=data['start'],
                        confidence=1.0
                    )
                    bboxes.append(bbox)

            # 解析终止物体
            if 'end' in data and 'end_xyxy' in data:
                end_coords = data['end_xyxy']
                if len(end_coords) == 2 and len(end_coords[0]) == 2 and len(end_coords[1]) == 2:
                    bbox = BoundingBox(
                        x1=int(end_coords[0][0]),
                        y1=int(end_coords[0][1]),
                        x2=int(end_coords[1][0]),
                        y2=int(end_coords[1][1]),
                        label=data['end'],
                        confidence=1.0
                    )
                    bboxes.append(bbox)

            confidence = 0.9 if bboxes else 0.0
            return bboxes, confidence

        except Exception as e:
            logger.warning(f"Failed to parse grounding response: {e}")
            return None, None

    def _create_test_image(self, image_path: str):
        """创建测试图像"""
        try:
            from PIL import Image, ImageDraw
            import os

            # 确保目录存在
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            # 创建简单的测试图像
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)

            # 画一些简单的形状
            draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
            draw.rectangle([200, 100, 300, 200], fill='blue', outline='black')

            img.save(image_path)
            logger.debug(f"Test image created: {image_path}")

        except Exception as e:
            logger.error(f"Failed to create test image: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = super().get_model_info()
        info.update({
            'provider': 'openai',
            'supports_grounding': True,
            'supports_vqa': True,
            'available_models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-vision-preview'],
        })
        return info