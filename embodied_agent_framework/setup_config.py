#!/usr/bin/env python3
"""
Configuration Setup Script - 配置设置助手
帮助用户设置API密钥和环境变量
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
import inquirer
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from embodied_agent.utils.config import ConfigManager


class ConfigSetup:
    """配置设置助手"""

    def __init__(self):
        """初始化配置设置"""
        self.config_manager = ConfigManager()
        self.env_vars = {}

    def run_setup(self):
        """运行配置设置流程"""
        print("🤖 具身智能体框架 - 配置设置助手")
        print("=" * 60)
        print("这个助手将帮助您配置API密钥和环境变量")
        print()

        # 1. 创建默认配置文件
        self._create_default_configs()

        # 2. 设置API密钥
        self._setup_api_keys()

        # 3. 设置硬件配置
        self._setup_hardware_config()

        # 4. 保存配置
        self._save_configuration()

        # 5. 验证配置
        self._validate_configuration()

        print("\n✅ 配置设置完成！")
        print("您现在可以运行测试脚本来验证配置:")
        print("  python tests/test_system.py    # 完整系统测试")
        print("  python tests/test_models.py    # 模型连通性测试")
        print("  python tests/test_hardware.py  # 硬件设备测试")

    def _create_default_configs(self):
        """创建默认配置文件"""
        print("📁 创建默认配置文件...")

        try:
            self.config_manager.create_default_configs()
            print("✅ 默认配置文件创建成功")
        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")
            sys.exit(1)

    def _setup_api_keys(self):
        """设置API密钥"""
        print("\n🔑 设置API密钥")
        print("-" * 30)

        # 私有化模型配置（必需）
        print("\n📍 私有化模型配置 (必需)")
        self.env_vars['PRIVATE_API_KEY'] = self._get_input(
            "请输入私有模型API密钥",
            required=True,
            secret=True
        )

        self.env_vars['PRIVATE_BASE_URL'] = self._get_input(
            "请输入私有模型服务地址",
            default="http://localhost:8000/v1",
            required=True
        )

        self.env_vars['PRIVATE_LLM_MODEL'] = self._get_input(
            "请输入文本模型名称",
            required=True
        )

        self.env_vars['PRIVATE_VLM_MODEL'] = self._get_input(
            "请输入视觉模型名称",
            required=True
        )

        # 在线模型配置（可选）
        print("\n🌐 在线模型配置 (可选)")

        if self._ask_yes_no("是否配置零一万物(Yi)模型API？"):
            self.env_vars['YI_KEY'] = self._get_input(
                "请输入零一万物API密钥",
                secret=True
            )

        if self._ask_yes_no("是否配置通义千问(Qwen)模型API？"):
            self.env_vars['QWEN_KEY'] = self._get_input(
                "请输入通义千问API密钥",
                secret=True
            )

        if self._ask_yes_no("是否配置OpenAI模型API？"):
            self.env_vars['OPENAI_API_KEY'] = self._get_input(
                "请输入OpenAI API密钥",
                secret=True
            )

        if self._ask_yes_no("是否配置百度AppBuilder（用于TTS/ASR）？"):
            self.env_vars['APPBUILDER_TOKEN'] = self._get_input(
                "请输入AppBuilder Token",
                secret=True
            )

    def _setup_hardware_config(self):
        """设置硬件配置"""
        print("\n🔧 设置硬件配置")
        print("-" * 30)

        # 机械臂配置
        if self._ask_yes_no("是否配置机械臂串口？"):
            robot_port = self._get_input(
                "请输入机械臂串口地址",
                default="/dev/ttyUSB0"
            )
            if robot_port:
                self.env_vars['ROBOT_PORT'] = robot_port

        # 摄像头配置
        if self._ask_yes_no("是否修改摄像头索引？"):
            camera_index = self._get_input(
                "请输入摄像头索引号",
                default="0"
            )
            if camera_index.isdigit():
                # 更新硬件配置文件
                hardware_config = self.config_manager.load_config('hardware')
                hardware_config['camera']['camera_index'] = int(camera_index)
                self.config_manager.save_config('hardware', hardware_config)

        # 音频设备配置
        if self._ask_yes_no("是否配置音频设备？"):
            mic_index = self._get_input(
                "请输入麦克风设备索引号（留空使用默认）"
            )
            speaker_index = self._get_input(
                "请输入扬声器设备索引号（留空使用默认）"
            )

            if mic_index or speaker_index:
                hardware_config = self.config_manager.load_config('hardware')
                if mic_index and mic_index.isdigit():
                    hardware_config['audio']['input_device_index'] = int(mic_index)
                if speaker_index and speaker_index.isdigit():
                    hardware_config['audio']['output_device_index'] = int(speaker_index)
                self.config_manager.save_config('hardware', hardware_config)

    def _save_configuration(self):
        """保存配置到.env文件"""
        print("\n💾 保存配置...")

        env_file = Path("config/.env")
        env_file.parent.mkdir(exist_ok=True)

        # 读取现有.env文件（如果存在）
        existing_vars = {}
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_vars[key] = value

        # 合并新的环境变量
        all_vars = {**existing_vars, **self.env_vars}

        # 写入.env文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Embodied Agent Framework Environment Variables\n")
            f.write(f"# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 分组写入变量
            groups = {
                "Private Model Configuration": [
                    'PRIVATE_API_KEY', 'PRIVATE_BASE_URL',
                    'PRIVATE_LLM_MODEL', 'PRIVATE_VLM_MODEL'
                ],
                "Online Model APIs": [
                    'YI_KEY', 'QWEN_KEY', 'OPENAI_API_KEY', 'APPBUILDER_TOKEN'
                ],
                "Hardware Configuration": [
                    'ROBOT_PORT'
                ],
                "Development Settings": [
                    'DEBUG', 'LOG_LEVEL'
                ]
            }

            for group_name, var_names in groups.items():
                group_vars = [(name, all_vars.get(name)) for name in var_names if name in all_vars]
                if group_vars:
                    f.write(f"# {group_name}\n")
                    for var_name, var_value in group_vars:
                        f.write(f"{var_name}={var_value}\n")
                    f.write("\n")

        print(f"✅ 配置已保存到: {env_file}")

    def _validate_configuration(self):
        """验证配置"""
        print("\n🔍 验证配置...")

        # 重新加载配置管理器以读取新的.env文件
        self.config_manager = ConfigManager()

        validation_results = self.config_manager.validate_config()

        print("配置验证结果:")
        for check_name, result in validation_results.items():
            status_icon = "✅" if result else "❌"
            print(f"  {status_icon} {check_name}")

        if all(validation_results.values()):
            print("✅ 所有配置验证通过！")
        else:
            print("⚠️ 部分配置验证失败，请检查相关设置")

    def _get_input(self, prompt: str, default: str = "", required: bool = False, secret: bool = False) -> str:
        """获取用户输入"""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "

        if required:
            full_prompt = f"🔴 {full_prompt}"

        while True:
            if secret:
                import getpass
                value = getpass.getpass(full_prompt)
            else:
                value = input(full_prompt).strip()

            if not value and default:
                return default
            elif not value and required:
                print("❌ 此项为必填项，请输入有效值")
                continue
            else:
                return value

    def _ask_yes_no(self, question: str, default: bool = False) -> bool:
        """询问是非题"""
        default_text = "Y/n" if default else "y/N"
        response = input(f"{question} [{default_text}]: ").strip().lower()

        if not response:
            return default

        return response in ['y', 'yes', '是', '是的']


def main():
    """主函数"""
    try:
        setup = ConfigSetup()
        setup.run_setup()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消了配置设置")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 配置设置过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 导入需要的模块
    import time

    main()