"""
Configuration Management utilities
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv


class ConfigManager:
    """
    Configuration manager for the Embodied Agent Framework
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # Load environment variables
        env_file = self.config_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")

        # Configuration cache
        self._config_cache: Dict[str, Any] = {}

    def load_config(self, config_name: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Args:
            config_name: Name of configuration file (without extension)
            default: Default configuration if file doesn't exist

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if config_name in self._config_cache:
            return self._config_cache[config_name]

        config_file = self.config_dir / f"{config_name}.yaml"

        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_file}")
            else:
                config = default or {}
                logger.warning(f"Configuration file {config_file} not found, using defaults")

            # Replace environment variable placeholders
            config = self._resolve_env_vars(config)

            self._config_cache[config_name] = config
            return config

        except Exception as e:
            logger.error(f"Error loading configuration {config_name}: {e}")
            return default or {}

    def save_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration to YAML file

        Args:
            config_name: Name of configuration file (without extension)
            config: Configuration dictionary

        Returns:
            bool: True if save successful
        """
        try:
            config_file = self.config_dir / f"{config_name}.yaml"

            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            self._config_cache[config_name] = config
            logger.info(f"Saved configuration to {config_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration {config_name}: {e}")
            return False

    def get_env_var(self, var_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value

        Args:
            var_name: Environment variable name
            default: Default value if variable not set

        Returns:
            Optional[str]: Environment variable value
        """
        return os.getenv(var_name, default)

    def _resolve_env_vars(self, config: Any) -> Any:
        """
        Recursively resolve environment variable placeholders in configuration

        Args:
            config: Configuration value (can be dict, list, or string)

        Returns:
            Any: Configuration with resolved environment variables
        """
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Replace ${ENV_VAR} or ${ENV_VAR:default} patterns
            import re
            pattern = r'\$\{([^}]+)\}'

            def replace_env_var(match):
                env_expr = match.group(1)
                if ':' in env_expr:
                    env_name, default_val = env_expr.split(':', 1)
                    return os.getenv(env_name.strip(), default_val.strip())
                else:
                    return os.getenv(env_expr.strip(), match.group(0))

            return re.sub(pattern, replace_env_var, config)
        else:
            return config

    def create_default_configs(self):
        """Create default configuration files"""
        self._create_main_config()
        self._create_hardware_config()
        self._create_models_config()
        self._create_env_template()

    def _create_main_config(self):
        """Create main configuration file"""
        config = {
            'framework': {
                'name': 'EmbodiedAgent Framework',
                'version': '0.1.0',
                'log_level': 'INFO',
                'temp_directory': 'temp',
                'assets_directory': 'assets'
            },
            'fusion': {
                'context_window': 5.0,
                'confidence_threshold': 0.7,
                'fusion_frequency': 10.0,
                'object_persistence_time': 3.0
            },
            'safety': {
                'max_speed': 50,
                'safe_height': 200,
                'workspace_limits': {
                    'x': [-250, 250],
                    'y': [-250, 250],
                    'z': [50, 350]
                },
                'emergency_stop_enabled': True
            }
        }
        self.save_config('config', config)

    def _create_hardware_config(self):
        """Create hardware configuration file"""
        config = {
            'robot': {
                'type': 'mycobot',
                'port': '${ROBOT_PORT:/dev/ttyUSB0}',
                'baudrate': 115200,
                'simulation_mode': False,
                'suction_pin_1': 20,
                'suction_pin_2': 21,
                'default_speed': 40,
                'safe_height': 230
            },
            'camera': {
                'camera_index': 0,
                'resolution': [640, 480],
                'fps': 30,
                'auto_exposure': True,
                'brightness': 0,
                'contrast': 1.0,
                'save_directory': 'temp',
                'image_format': 'jpg'
            },
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'chunk_size': 1024,
                'input_device_index': null,
                'output_device_index': null,
                'recording_duration': 5,
                'voice_activation_threshold': 0.01,
                'silence_duration': 2.0,
                'save_directory': 'temp',
                'audio_format': 'wav'
            }
        }
        self.save_config('hardware', config)

    def _create_models_config(self):
        """Create models configuration file"""
        config = {
            'llm': {
                'default_provider': 'private',
                'providers': {
                    'openai': {
                        'api_key': '${OPENAI_API_KEY}',
                        'base_url': 'https://api.openai.com/v1',
                        'model_name': 'gpt-4',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    },
                    'yi': {
                        'api_key': '${YI_KEY}',
                        'base_url': 'https://api.lingyiwanwu.com/v1',
                        'model_name': 'yi-large',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    },
                    'private': {
                        'api_key': '${PRIVATE_API_KEY}',
                        'base_url': '${PRIVATE_BASE_URL}',
                        'model_name': '${PRIVATE_LLM_MODEL}',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    }
                }
            },
            'vlm': {
                'default_provider': 'private',
                'providers': {
                    'yi_vision': {
                        'api_key': '${YI_KEY}',
                        'base_url': 'https://api.lingyiwanwu.com/v1',
                        'model_name': 'yi-vision',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    },
                    'qwen_vl': {
                        'api_key': '${QWEN_KEY}',
                        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                        'model_name': 'qwen-vl-max-2024-11-19',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    },
                    'private': {
                        'api_key': '${PRIVATE_API_KEY}',
                        'base_url': '${PRIVATE_BASE_URL}',
                        'model_name': '${PRIVATE_VLM_MODEL}',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    }
                }
            },
            'tts': {
                'provider': 'appbuilder',
                'api_key': '${APPBUILDER_TOKEN}',
                'voice': 'zh-CN-XiaoxiaoNeural'
            },
            'asr': {
                'provider': 'appbuilder',
                'api_key': '${APPBUILDER_TOKEN}',
                'language': 'zh-CN'
            }
        }
        self.save_config('models', config)

    def _create_env_template(self):
        """Create environment variables template file"""
        env_content = """# Embodied Agent Framework Environment Variables
# Copy this file to .env and fill in your API keys

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Yi (零一万物) API Key
YI_KEY=your_yi_api_key_here

# Qwen (通义千问) API Key
QWEN_KEY=your_qwen_api_key_here

# AppBuilder Token (for TTS/ASR)
APPBUILDER_TOKEN=your_appbuilder_token_here

# Private Model Configuration
PRIVATE_API_KEY=your_private_api_key_here
PRIVATE_BASE_URL=http://localhost:8000/v1
PRIVATE_LLM_MODEL=your_text_model_name
PRIVATE_VLM_MODEL=your_vision_model_name

# Hardware Configuration
ROBOT_PORT=/dev/ttyUSB0

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
"""
        env_file = self.config_dir / ".env.example"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        logger.info(f"Created environment template at {env_file}")

    def get_robot_config(self) -> Dict[str, Any]:
        """Get robot hardware configuration"""
        hardware_config = self.load_config('hardware')
        return hardware_config.get('robot', {})

    def get_camera_config(self) -> Dict[str, Any]:
        """Get camera configuration"""
        hardware_config = self.load_config('hardware')
        return hardware_config.get('camera', {})

    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration"""
        hardware_config = self.load_config('hardware')
        return hardware_config.get('audio', {})

    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration"""
        models_config = self.load_config('models')
        llm_config = models_config.get('llm', {})

        if provider is None:
            provider = llm_config.get('default_provider', 'openai')

        provider_config = llm_config.get('providers', {}).get(provider, {})
        return provider_config

    def get_vlm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get VLM configuration"""
        models_config = self.load_config('models')
        vlm_config = models_config.get('vlm', {})

        if provider is None:
            provider = vlm_config.get('default_provider', 'yi_vision')

        provider_config = vlm_config.get('providers', {}).get(provider, {})
        return provider_config

    def validate_config(self) -> Dict[str, bool]:
        """
        Validate configuration completeness

        Returns:
            Dict[str, bool]: Validation results
        """
        results = {}

        # Check main config
        main_config = self.load_config('config')
        results['main_config'] = bool(main_config.get('framework'))

        # Check hardware config
        hardware_config = self.load_config('hardware')
        results['hardware_config'] = bool(
            hardware_config.get('robot') and
            hardware_config.get('camera') and
            hardware_config.get('audio')
        )

        # Check models config
        models_config = self.load_config('models')
        results['models_config'] = bool(
            models_config.get('llm') and
            models_config.get('vlm')
        )

        # Check environment variables
        required_env_vars = [
            'PRIVATE_API_KEY', 'PRIVATE_BASE_URL',
            'PRIVATE_LLM_MODEL', 'PRIVATE_VLM_MODEL'
        ]
        results['env_variables'] = all(
            os.getenv(var) for var in required_env_vars
        )

        return results