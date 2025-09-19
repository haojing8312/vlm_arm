#!/usr/bin/env python3
"""
Model Connectivity Tests - 测试各种AI模型的连通性
"""

import asyncio
import sys
from pathlib import Path
import json
import time
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embodied_agent.utils.config import ConfigManager


class ModelTester:
    """AI模型连通性测试器"""

    def __init__(self):
        """初始化测试器"""
        self.config_manager = ConfigManager()
        self.test_results = {}

    async def test_all_models(self):
        """测试所有模型连通性"""
        logger.info("🧠 开始测试AI模型连通性")

        # 测试私有化模型
        await self._test_private_llm()
        await self._test_private_vlm()

        # 测试在线模型
        await self._test_yi_models()
        await self._test_qwen_models()
        await self._test_appbuilder_models()

        self._generate_model_report()

    async def _test_private_llm(self):
        """测试私有化部署的文本模型"""
        logger.info("🔧 测试私有化文本模型...")

        try:
            # 从原项目导入测试函数
            from agent_demo_20250328.utils_llm import test_private_llm

            # 测试连通性
            response = test_private_llm("你好，请简单回复确认连接正常")

            self.test_results['private_llm'] = {
                'status': 'success',
                'response': response,
                'message': '私有化文本模型连接正常'
            }
            logger.success("✅ 私有化文本模型测试通过")

        except ImportError:
            self.test_results['private_llm'] = {
                'status': 'warning',
                'message': '找不到原项目的测试函数，请手动测试'
            }
            logger.warning("⚠️ 找不到原项目的测试函数")

        except Exception as e:
            self.test_results['private_llm'] = {
                'status': 'failed',
                'error': str(e),
                'message': '私有化文本模型连接失败'
            }
            logger.error(f"❌ 私有化文本模型测试失败: {e}")

    async def _test_private_vlm(self):
        """测试私有化部署的视觉模型"""
        logger.info("👁️ 测试私有化视觉模型...")

        try:
            # 从原项目导入测试函数
            from agent_demo_20250328.utils_vlm import private_vlm_api

            # 创建测试图片（如果不存在）
            test_image_path = 'tests/test_image.jpg'
            if not Path(test_image_path).exists():
                self._create_test_image(test_image_path)

            # 测试视觉问答
            response = private_vlm_api(
                PROMPT="请描述这张图片中的内容",
                img_path=test_image_path,
                vlm_option=1  # VQA模式
            )

            self.test_results['private_vlm'] = {
                'status': 'success',
                'response': response,
                'message': '私有化视觉模型连接正常'
            }
            logger.success("✅ 私有化视觉模型测试通过")

        except ImportError:
            self.test_results['private_vlm'] = {
                'status': 'warning',
                'message': '找不到原项目的测试函数，请手动测试'
            }
            logger.warning("⚠️ 找不到原项目的测试函数")

        except Exception as e:
            self.test_results['private_vlm'] = {
                'status': 'failed',
                'error': str(e),
                'message': '私有化视觉模型连接失败'
            }
            logger.error(f"❌ 私有化视觉模型测试失败: {e}")

    async def _test_yi_models(self):
        """测试零一万物模型"""
        logger.info("🌟 测试零一万物模型...")

        try:
            from agent_demo_20250328.utils_llm import llm_yi
            from agent_demo_20250328.utils_vlm import yi_vision_api

            # 测试文本模型
            try:
                messages = [{"role": "user", "content": "你好，请简单回复确认连接正常"}]
                llm_response = llm_yi(messages)
                yi_llm_status = 'success'
                yi_llm_message = '连接正常'
            except Exception as e:
                yi_llm_status = 'failed'
                yi_llm_message = str(e)

            # 测试视觉模型
            try:
                test_image_path = 'tests/test_image.jpg'
                if not Path(test_image_path).exists():
                    self._create_test_image(test_image_path)

                vlm_response = yi_vision_api(
                    PROMPT="请描述这张图片",
                    img_path=test_image_path,
                    vlm_option=1
                )
                yi_vlm_status = 'success'
                yi_vlm_message = '连接正常'
            except Exception as e:
                yi_vlm_status = 'failed'
                yi_vlm_message = str(e)

            self.test_results['yi_models'] = {
                'llm': {'status': yi_llm_status, 'message': yi_llm_message},
                'vlm': {'status': yi_vlm_status, 'message': yi_vlm_message}
            }

            if yi_llm_status == 'success' and yi_vlm_status == 'success':
                logger.success("✅ 零一万物模型测试通过")
            else:
                logger.warning("⚠️ 零一万物模型部分测试失败")

        except ImportError:
            self.test_results['yi_models'] = {
                'status': 'warning',
                'message': '找不到原项目的测试函数'
            }
            logger.warning("⚠️ 找不到零一万物模型测试函数")

    async def _test_qwen_models(self):
        """测试通义千问模型"""
        logger.info("🚀 测试通义千问模型...")

        try:
            from agent_demo_20250328.utils_vlm import QwenVL_api

            # 测试视觉模型
            test_image_path = 'tests/test_image.jpg'
            if not Path(test_image_path).exists():
                self._create_test_image(test_image_path)

            response = QwenVL_api(
                PROMPT="请描述这张图片",
                img_path=test_image_path,
                vlm_option=1
            )

            self.test_results['qwen_vlm'] = {
                'status': 'success',
                'response': response,
                'message': '通义千问视觉模型连接正常'
            }
            logger.success("✅ 通义千问模型测试通过")

        except ImportError:
            self.test_results['qwen_vlm'] = {
                'status': 'warning',
                'message': '找不到原项目的测试函数'
            }
            logger.warning("⚠️ 找不到通义千问模型测试函数")

        except Exception as e:
            self.test_results['qwen_vlm'] = {
                'status': 'failed',
                'error': str(e),
                'message': '通义千问模型连接失败'
            }
            logger.error(f"❌ 通义千问模型测试失败: {e}")

    async def _test_appbuilder_models(self):
        """测试AppBuilder模型（TTS/ASR）"""
        logger.info("🎙️ 测试AppBuilder模型...")

        try:
            from agent_demo_20250328.utils_asr import speech_recognition
            from agent_demo_20250328.utils_tts import tts

            # 测试TTS
            try:
                tts("这是一个测试")
                tts_status = 'success'
                tts_message = 'TTS功能正常'
            except Exception as e:
                tts_status = 'failed'
                tts_message = str(e)

            # 测试ASR（需要音频文件）
            try:
                # 这里需要有测试音频文件
                test_audio = 'tests/test_audio.wav'
                if Path(test_audio).exists():
                    result = speech_recognition(test_audio)
                    asr_status = 'success'
                    asr_message = 'ASR功能正常'
                else:
                    asr_status = 'warning'
                    asr_message = '没有测试音频文件'
            except Exception as e:
                asr_status = 'failed'
                asr_message = str(e)

            self.test_results['appbuilder'] = {
                'tts': {'status': tts_status, 'message': tts_message},
                'asr': {'status': asr_status, 'message': asr_message}
            }

            if tts_status == 'success':
                logger.success("✅ AppBuilder TTS测试通过")
            if asr_status == 'success':
                logger.success("✅ AppBuilder ASR测试通过")

        except ImportError:
            self.test_results['appbuilder'] = {
                'status': 'warning',
                'message': '找不到原项目的TTS/ASR函数'
            }
            logger.warning("⚠️ 找不到AppBuilder模型测试函数")

    def _create_test_image(self, image_path: str):
        """创建测试图片"""
        try:
            from PIL import Image, ImageDraw
            import numpy as np

            # 创建一个简单的测试图片
            img = Image.new('RGB', (640, 480), color='white')
            draw = ImageDraw.Draw(img)

            # 画一些简单的图形
            draw.rectangle([100, 100, 200, 200], fill='red', outline='black')
            draw.rectangle([300, 200, 400, 300], fill='green', outline='black')
            draw.rectangle([150, 300, 250, 400], fill='blue', outline='black')

            # 保存图片
            Path(image_path).parent.mkdir(exist_ok=True)
            img.save(image_path)
            logger.info(f"创建测试图片: {image_path}")

        except Exception as e:
            logger.error(f"创建测试图片失败: {e}")

    def _generate_model_report(self):
        """生成模型测试报告"""
        logger.info("📊 生成模型测试报告...")

        report_lines = [
            "=" * 60,
            "AI模型连通性测试报告",
            "=" * 60,
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "模型测试结果:",
            "-" * 30
        ]

        for model_name, result in self.test_results.items():
            if isinstance(result, dict) and 'status' in result:
                status_icon = {
                    'success': '✅',
                    'failed': '❌',
                    'warning': '⚠️'
                }.get(result['status'], '❓')
                report_lines.append(f"{status_icon} {model_name}: {result['message']}")
            else:
                # 处理复合结果（如yi_models）
                report_lines.append(f"📋 {model_name}:")
                for sub_model, sub_result in result.items():
                    if isinstance(sub_result, dict) and 'status' in sub_result:
                        status_icon = {
                            'success': '✅',
                            'failed': '❌',
                            'warning': '⚠️'
                        }.get(sub_result['status'], '❓')
                        report_lines.append(f"  {status_icon} {sub_model}: {sub_result['message']}")

        report_lines.extend([
            "",
            "=" * 60,
            "配置建议:",
            "-" * 30,
            "如果测试失败，请检查以下配置:",
            "",
            "1. 环境变量配置 (.env 文件):",
            "   - PRIVATE_API_KEY=你的私有模型API密钥",
            "   - PRIVATE_BASE_URL=你的私有模型服务地址",
            "   - PRIVATE_LLM_MODEL=你的文本模型名称",
            "   - PRIVATE_VLM_MODEL=你的视觉模型名称",
            "   - YI_KEY=零一万物API密钥",
            "   - QWEN_KEY=通义千问API密钥",
            "   - APPBUILDER_TOKEN=百度AppBuilder密钥",
            "",
            "2. 网络连接:",
            "   - 确保可以访问相应的API服务",
            "   - 检查防火墙和代理设置",
            "",
            "3. API配额:",
            "   - 确认API密钥有足够的调用配额",
            "   - 检查是否有调用频率限制",
            "=" * 60
        ])

        report_content = "\n".join(report_lines)

        # 保存到文件
        report_file = Path("tests/model_test_report.txt")
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 输出到控制台
        print(report_content)

        logger.info(f"📋 模型测试报告已保存到: {report_file}")


async def main():
    """主函数"""
    print("🧠 AI模型连通性测试")
    print("=" * 50)

    # 创建测试目录
    Path("tests").mkdir(exist_ok=True)

    # 运行测试
    tester = ModelTester()
    await tester.test_all_models()


if __name__ == "__main__":
    asyncio.run(main())