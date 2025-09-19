#!/usr/bin/env python3
"""
Quick Start Script - 快速启动脚本
帮助用户快速开始使用具身智能体框架
"""

import sys
import os
import asyncio
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🤖 具身智能体框架 (Embodied Agent Framework)             ║
    ║                                                              ║
    ║     一个标准化的机械臂+AI大模型+多模态感知的开发框架           ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印主菜单"""
    menu = """
    请选择您要执行的操作:

    📋 配置和设置:
      1. 配置设置助手         - 设置API密钥和硬件配置
      2. 查看当前配置         - 显示当前的配置信息

    🧪 测试和验证:
      3. 完整系统测试         - 测试所有组件的功能和连通性
      4. 模型连通性测试       - 测试AI模型API连接
      5. 硬件设备测试         - 测试机械臂、摄像头、音频设备

    🚀 应用示例:
      6. 运行AI学伴演示       - 启动AI学习助手应用
      7. 基础功能演示         - 演示基本的机械臂控制功能

    📚 帮助和文档:
      8. 查看使用说明         - 显示详细的使用指南
      9. 查看API文档          - 显示开发文档

      0. 退出程序

    """
    print(menu)


async def run_config_setup():
    """运行配置设置"""
    print("🔧 启动配置设置助手...")
    try:
        from setup_config import ConfigSetup
        setup = ConfigSetup()
        setup.run_setup()
    except Exception as e:
        print(f"❌ 配置设置失败: {e}")


async def show_current_config():
    """显示当前配置"""
    print("📋 当前配置信息:")
    print("-" * 50)

    try:
        from embodied_agent.utils.config import ConfigManager
        config_manager = ConfigManager()

        # 显示配置验证结果
        validation_results = config_manager.validate_config()
        print("\n配置状态:")
        for check_name, result in validation_results.items():
            status_icon = "✅" if result else "❌"
            print(f"  {status_icon} {check_name.replace('_', ' ').title()}")

        # 显示主要配置
        print("\n主要配置:")
        main_config = config_manager.load_config('config')
        if main_config:
            print(f"  - 框架版本: {main_config.get('framework', {}).get('version', 'unknown')}")
            print(f"  - 日志级别: {main_config.get('framework', {}).get('log_level', 'INFO')}")

        # 显示模型配置
        models_config = config_manager.load_config('models')
        if models_config:
            llm_provider = models_config.get('llm', {}).get('default_provider', 'unknown')
            vlm_provider = models_config.get('vlm', {}).get('default_provider', 'unknown')
            print(f"  - 默认LLM提供商: {llm_provider}")
            print(f"  - 默认VLM提供商: {vlm_provider}")

        # 显示环境变量状态
        print("\n环境变量状态:")
        required_vars = [
            'PRIVATE_API_KEY', 'PRIVATE_BASE_URL',
            'PRIVATE_LLM_MODEL', 'PRIVATE_VLM_MODEL'
        ]
        for var in required_vars:
            value = os.getenv(var)
            status = "✅ 已设置" if value else "❌ 未设置"
            print(f"  - {var}: {status}")

    except Exception as e:
        print(f"❌ 读取配置失败: {e}")


async def run_system_test():
    """运行完整系统测试"""
    print("🧪 启动完整系统测试...")
    try:
        from tests.test_system import main as test_main
        await test_main()
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")


async def run_model_test():
    """运行模型连通性测试"""
    print("🧠 启动模型连通性测试...")
    try:
        from tests.test_models import main as test_main
        await test_main()
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")


async def run_hardware_test():
    """运行硬件设备测试"""
    print("🔧 启动硬件设备测试...")
    try:
        from tests.test_hardware import main as test_main
        await test_main()
    except Exception as e:
        print(f"❌ 硬件测试失败: {e}")


async def run_ai_tutor_demo():
    """运行AI学伴演示"""
    print("🎓 启动AI学伴演示...")
    print("⚠️ AI学伴应用还在开发中，敬请期待！")
    # TODO: 实现AI学伴应用


async def run_basic_demo():
    """运行基础功能演示"""
    print("🤖 启动基础功能演示...")

    try:
        # 检查是否有原项目的演示代码
        demo_path = Path("../agent_demo_20250328/agent_go.py")
        if demo_path.exists():
            print("找到原项目演示代码，是否运行原版演示？(y/n): ", end="")
            response = input().strip().lower()
            if response in ['y', 'yes', '是']:
                print("请在原项目目录中运行: python agent_go.py")
                return

        print("运行框架基础功能演示...")
        # TODO: 实现基础功能演示
        print("⚠️ 基础功能演示还在开发中，请先运行测试脚本验证功能！")

    except Exception as e:
        print(f"❌ 演示运行失败: {e}")


def show_usage_guide():
    """显示使用说明"""
    guide = """
    ══════════════════════════════════════════════════════════════
                              使用说明
    ══════════════════════════════════════════════════════════════

    📋 快速开始流程:

    1. 首次使用:
       ① 运行 "配置设置助手" 设置API密钥和硬件配置
       ② 运行 "完整系统测试" 验证所有组件功能
       ③ 根据测试结果调整配置

    2. 开发使用:
       ① 导入框架: from embodied_agent import *
       ② 创建组件: 机械臂控制器、视觉处理器等
       ③ 编写应用逻辑

    📚 目录结构:

    embodied_agent_framework/
    ├── embodied_agent/          # 核心框架库
    │   ├── core/                # 核心组件
    │   ├── interfaces/          # 接口层
    │   ├── hardware/            # 硬件适配器
    │   ├── agents/              # 智能体层
    │   └── utils/               # 工具模块
    ├── apps/                    # 应用层
    ├── tests/                   # 测试代码
    ├── config/                  # 配置文件
    └── docs/                    # 文档

    🔧 配置文件:

    - config/config.yaml         # 主配置文件
    - config/hardware.yaml       # 硬件配置
    - config/models.yaml         # 模型配置
    - config/.env                # 环境变量（API密钥等）

    🚨 注意事项:

    - 确保硬件设备已正确连接
    - API密钥需要有足够的调用配额
    - 网络连接要稳定
    - 树莓派环境需要sudo权限运行GPIO相关功能

    ══════════════════════════════════════════════════════════════
    """
    print(guide)


def show_api_docs():
    """显示API文档"""
    docs = """
    ══════════════════════════════════════════════════════════════
                              API文档
    ══════════════════════════════════════════════════════════════

    🤖 机械臂控制 (RobotController):

    ```python
    from embodied_agent import RobotController
    from embodied_agent.hardware.mycobot import MyCobotAdapter

    # 创建机械臂控制器
    config = {'port': '/dev/ttyUSB0', 'baudrate': 115200}
    adapter = MyCobotAdapter(config)
    robot = RobotController(adapter, config)

    # 初始化
    await robot.initialize()

    # 基本控制
    await robot.move_to_position(150, -120, 200)
    await robot.pick_and_place((100, 100, 90), (200, 200, 90))
    await robot.move_to_home()
    ```

    👁️ 视觉处理 (VisionProcessor):

    ```python
    from embodied_agent import VisionProcessor

    # 创建视觉处理器
    config = {'camera_index': 0, 'resolution': [640, 480]}
    vision = VisionProcessor(config)

    # 初始化和拍照
    await vision.initialize()
    frame = await vision.capture_image('photo.jpg')

    # 物体检测
    color_ranges = {
        'red_object': {'lower': (0, 50, 50), 'upper': (10, 255, 255)}
    }
    detections = await vision.detect_objects_color(color_ranges)
    ```

    🎙️ 音频处理 (AudioProcessor):

    ```python
    from embodied_agent import AudioProcessor

    # 创建音频处理器
    config = {'sample_rate': 16000, 'channels': 1}
    audio = AudioProcessor(config)

    # 录音和播放
    await audio.initialize()
    recording = await audio.record_fixed_duration(5.0)
    await audio.play_audio_file('audio.wav')
    ```

    🧠 多模态融合 (MultiModalFusion):

    ```python
    from embodied_agent import MultiModalFusion

    # 创建多模态融合器
    fusion = MultiModalFusion({})
    fusion.set_vision_processor(vision)
    fusion.set_audio_processor(audio)
    fusion.set_robot_controller(robot)

    # 启动融合
    await fusion.start_fusion()
    context = fusion.get_current_context()
    ```

    📋 配置管理 (ConfigManager):

    ```python
    from embodied_agent.utils.config import ConfigManager

    # 加载配置
    config_manager = ConfigManager()
    robot_config = config_manager.get_robot_config()
    llm_config = config_manager.get_llm_config('private')
    ```

    ══════════════════════════════════════════════════════════════
    """
    print(docs)


async def main_menu():
    """主菜单循环"""
    while True:
        print_menu()

        try:
            choice = input("请输入选项编号 (0-9): ").strip()

            if choice == "0":
                print("👋 感谢使用具身智能体框架！")
                break
            elif choice == "1":
                await run_config_setup()
            elif choice == "2":
                await show_current_config()
            elif choice == "3":
                await run_system_test()
            elif choice == "4":
                await run_model_test()
            elif choice == "5":
                await run_hardware_test()
            elif choice == "6":
                await run_ai_tutor_demo()
            elif choice == "7":
                await run_basic_demo()
            elif choice == "8":
                show_usage_guide()
            elif choice == "9":
                show_api_docs()
            else:
                print("❌ 无效选项，请输入 0-9 之间的数字")

            input("\n按回车键继续...")
            print("\n" + "="*60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 感谢使用具身智能体框架！")
            break
        except Exception as e:
            print(f"\n❌ 操作失败: {e}")
            input("按回车键继续...")


async def main():
    """主函数"""
    print_banner()

    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)

    # 创建必要的目录
    for directory in ['config', 'tests', 'temp', 'logs']:
        Path(directory).mkdir(exist_ok=True)

    await main_menu()


if __name__ == "__main__":
    asyncio.run(main())