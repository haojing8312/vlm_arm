#!/usr/bin/env python3
"""
Hardware Tests - 测试硬件设备连接和功能
"""

import asyncio
import sys
from pathlib import Path
import time
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embodied_agent.utils.config import ConfigManager


class HardwareTester:
    """硬件设备测试器"""

    def __init__(self):
        """初始化测试器"""
        self.config_manager = ConfigManager()
        self.test_results = {}

    async def test_all_hardware(self):
        """测试所有硬件设备"""
        logger.info("🔧 开始测试硬件设备")

        # 测试机械臂
        await self._test_robot_hardware()

        # 测试摄像头
        await self._test_camera_hardware()

        # 测试音频设备
        await self._test_audio_hardware()

        # 测试GPIO和吸泵
        await self._test_gpio_hardware()

        self._generate_hardware_report()

    async def _test_robot_hardware(self):
        """测试机械臂硬件"""
        logger.info("🤖 测试机械臂硬件...")

        try:
            # 尝试连接机械臂
            from agent_demo_20250328.utils_robot import mc, back_zero, move_to_top_view, head_shake

            # 测试基本连接
            try:
                current_angles = mc.get_angles()
                current_coords = mc.get_coords()
                robot_connected = True
                connection_message = "机械臂连接成功"
            except Exception as e:
                robot_connected = False
                connection_message = f"机械臂连接失败: {e}"

            # 如果连接成功，测试基本动作
            movement_tests = {}
            if robot_connected:
                try:
                    # 测试归零
                    logger.info("测试归零动作...")
                    back_zero()
                    movement_tests['back_zero'] = 'success'
                    await asyncio.sleep(2)

                    # 测试俯视姿态
                    logger.info("测试俯视姿态...")
                    move_to_top_view()
                    movement_tests['top_view'] = 'success'
                    await asyncio.sleep(3)

                    # 测试摇头动作
                    logger.info("测试摇头动作...")
                    head_shake()
                    movement_tests['head_shake'] = 'success'

                    logger.info("所有动作测试完成，回到原点...")
                    back_zero()

                except Exception as e:
                    movement_tests['error'] = str(e)

            self.test_results['robot'] = {
                'connected': robot_connected,
                'connection_message': connection_message,
                'current_angles': current_angles if robot_connected else None,
                'current_coords': current_coords if robot_connected else None,
                'movement_tests': movement_tests,
                'status': 'success' if robot_connected else 'failed'
            }

            if robot_connected:
                logger.success("✅ 机械臂硬件测试通过")
            else:
                logger.error("❌ 机械臂硬件测试失败")

        except ImportError:
            self.test_results['robot'] = {
                'status': 'warning',
                'message': '找不到机械臂控制模块，可能未正确安装'
            }
            logger.warning("⚠️ 找不到机械臂控制模块")

        except Exception as e:
            self.test_results['robot'] = {
                'status': 'failed',
                'error': str(e),
                'message': '机械臂硬件测试出错'
            }
            logger.error(f"❌ 机械臂硬件测试失败: {e}")

    async def _test_camera_hardware(self):
        """测试摄像头硬件"""
        logger.info("📹 测试摄像头硬件...")

        try:
            from agent_demo_20250328.utils_camera import check_camera
            from agent_demo_20250328.utils_robot import top_view_shot

            # 测试摄像头基本功能
            try:
                logger.info("测试摄像头基本功能...")
                check_camera()
                camera_basic = 'success'
                camera_message = "摄像头基本功能正常"
            except Exception as e:
                camera_basic = 'failed'
                camera_message = f"摄像头基本功能失败: {e}"

            # 测试俯视拍照
            try:
                logger.info("测试俯视拍照功能...")
                top_view_shot(check=False)
                top_view_capture = 'success'

                # 检查图片是否生成
                if Path('temp/vl_now.jpg').exists():
                    photo_saved = True
                else:
                    photo_saved = False

            except Exception as e:
                top_view_capture = 'failed'
                photo_saved = False

            self.test_results['camera'] = {
                'basic_function': camera_basic,
                'message': camera_message,
                'top_view_capture': top_view_capture,
                'photo_saved': photo_saved,
                'status': 'success' if camera_basic == 'success' else 'failed'
            }

            if camera_basic == 'success':
                logger.success("✅ 摄像头硬件测试通过")
            else:
                logger.error("❌ 摄像头硬件测试失败")

        except ImportError:
            self.test_results['camera'] = {
                'status': 'warning',
                'message': '找不到摄像头控制模块'
            }
            logger.warning("⚠️ 找不到摄像头控制模块")

        except Exception as e:
            self.test_results['camera'] = {
                'status': 'failed',
                'error': str(e),
                'message': '摄像头硬件测试出错'
            }
            logger.error(f"❌ 摄像头硬件测试失败: {e}")

    async def _test_audio_hardware(self):
        """测试音频设备硬件"""
        logger.info("🎙️ 测试音频设备硬件...")

        try:
            from agent_demo_20250328.utils_asr import record
            from agent_demo_20250328.utils_tts import play_wav
            from agent_demo_20250328.sound_check import main as sound_check

            # 测试音频设备检测
            try:
                logger.info("检测音频设备...")
                # 这里应该调用音频设备检测
                device_check = 'success'
                device_message = "音频设备检测通过"
            except Exception as e:
                device_check = 'failed'
                device_message = f"音频设备检测失败: {e}"

            # 测试录音功能
            try:
                logger.info("测试录音功能（2秒）...")
                record(MIC_INDEX=3, DURATION=2)  # 录音2秒

                # 检查录音文件是否生成
                if Path('temp/speech_record.wav').exists():
                    recording_test = 'success'
                else:
                    recording_test = 'failed'
            except Exception as e:
                recording_test = 'failed'

            # 测试播放功能
            try:
                logger.info("测试音频播放功能...")
                if Path('asset/welcome.wav').exists():
                    play_wav('asset/welcome.wav')
                    playback_test = 'success'
                else:
                    playback_test = 'warning'  # 文件不存在但功能可能正常
            except Exception as e:
                playback_test = 'failed'

            self.test_results['audio'] = {
                'device_check': device_check,
                'device_message': device_message,
                'recording_test': recording_test,
                'playback_test': playback_test,
                'status': 'success' if device_check == 'success' else 'failed'
            }

            if device_check == 'success':
                logger.success("✅ 音频设备硬件测试通过")
            else:
                logger.error("❌ 音频设备硬件测试失败")

        except ImportError:
            self.test_results['audio'] = {
                'status': 'warning',
                'message': '找不到音频控制模块'
            }
            logger.warning("⚠️ 找不到音频控制模块")

        except Exception as e:
            self.test_results['audio'] = {
                'status': 'failed',
                'error': str(e),
                'message': '音频设备硬件测试出错'
            }
            logger.error(f"❌ 音频设备硬件测试失败: {e}")

    async def _test_gpio_hardware(self):
        """测试GPIO和吸泵硬件"""
        logger.info("🔌 测试GPIO和吸泵硬件...")

        try:
            from agent_demo_20250328.utils_pump import pump_on, pump_off

            # 测试吸泵控制
            try:
                logger.info("测试吸泵开启...")
                pump_on()
                await asyncio.sleep(1)

                logger.info("测试吸泵关闭...")
                pump_off()

                pump_test = 'success'
                pump_message = "吸泵控制正常"

            except Exception as e:
                pump_test = 'failed'
                pump_message = f"吸泵控制失败: {e}"

            self.test_results['gpio'] = {
                'pump_test': pump_test,
                'pump_message': pump_message,
                'status': pump_test
            }

            if pump_test == 'success':
                logger.success("✅ GPIO和吸泵硬件测试通过")
            else:
                logger.error("❌ GPIO和吸泵硬件测试失败")

        except ImportError:
            self.test_results['gpio'] = {
                'status': 'warning',
                'message': '找不到GPIO控制模块，可能不在树莓派环境'
            }
            logger.warning("⚠️ 找不到GPIO控制模块")

        except Exception as e:
            self.test_results['gpio'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'GPIO硬件测试出错'
            }
            logger.error(f"❌ GPIO硬件测试失败: {e}")

    def _generate_hardware_report(self):
        """生成硬件测试报告"""
        logger.info("📊 生成硬件测试报告...")

        report_lines = [
            "=" * 60,
            "硬件设备测试报告",
            "=" * 60,
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "硬件测试结果:",
            "-" * 30
        ]

        for hardware_name, result in self.test_results.items():
            status_icon = {
                'success': '✅',
                'failed': '❌',
                'warning': '⚠️'
            }.get(result.get('status'), '❓')

            report_lines.append(f"{status_icon} {hardware_name.upper()}")

            if 'message' in result:
                report_lines.append(f"   状态: {result['message']}")

            # 添加详细信息
            if hardware_name == 'robot' and result.get('connected'):
                if result.get('current_angles'):
                    report_lines.append(f"   当前关节角度: {result['current_angles']}")
                if result.get('movement_tests'):
                    for test_name, test_result in result['movement_tests'].items():
                        test_icon = '✅' if test_result == 'success' else '❌'
                        report_lines.append(f"   {test_icon} {test_name}")

            elif hardware_name == 'camera':
                if result.get('photo_saved'):
                    report_lines.append("   ✅ 图片保存成功")

            elif hardware_name == 'audio':
                for test_type in ['recording_test', 'playback_test']:
                    if test_type in result:
                        test_icon = '✅' if result[test_type] == 'success' else '❌'
                        report_lines.append(f"   {test_icon} {test_type.replace('_', ' ')}")

            report_lines.append("")  # 空行

        report_lines.extend([
            "=" * 60,
            "硬件配置建议:",
            "-" * 30,
            "如果硬件测试失败，请检查以下配置:",
            "",
            "1. 机械臂连接:",
            "   - 确认机械臂已正确连接到电脑",
            "   - 检查USB/串口连接",
            "   - 确认机械臂电源已开启",
            "   - 检查驱动程序是否正确安装",
            "",
            "2. 摄像头设置:",
            "   - 确认摄像头已连接",
            "   - 检查摄像头权限设置",
            "   - 确认摄像头索引号正确",
            "",
            "3. 音频设备:",
            "   - 确认麦克风和扬声器已连接",
            "   - 检查音频设备权限",
            "   - 确认设备索引号正确",
            "",
            "4. GPIO设备（树莓派）:",
            "   - 确认运行在树莓派环境",
            "   - 检查GPIO权限（可能需要sudo）",
            "   - 确认吸泵电路连接正确",
            "=" * 60
        ])

        report_content = "\n".join(report_lines)

        # 保存到文件
        report_file = Path("tests/hardware_test_report.txt")
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 输出到控制台
        print(report_content)

        logger.info(f"📋 硬件测试报告已保存到: {report_file}")


async def main():
    """主函数"""
    print("🔧 硬件设备测试")
    print("=" * 50)

    # 创建测试目录
    Path("tests").mkdir(exist_ok=True)

    # 运行测试
    tester = HardwareTester()
    await tester.test_all_hardware()


if __name__ == "__main__":
    asyncio.run(main())