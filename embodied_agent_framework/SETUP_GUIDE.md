# 🤖 具身智能体框架 - 配置和使用指南

## 📋 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [配置设置](#配置设置)
- [测试验证](#测试验证)
- [使用示例](#使用示例)
- [故障排除](#故障排除)

## 🚀 快速开始

### 1. 一键启动
```bash
# 进入项目目录
cd embodied_agent_framework

# 运行快速启动脚本
python quick_start.py
```

### 2. 选择配置设置助手
在菜单中选择 `1. 配置设置助手`，按照提示完成配置。

### 3. 运行测试验证
配置完成后，选择 `3. 完整系统测试` 验证所有功能。

## 💻 环境要求

### 系统要求
- **操作系统**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+
- **Python版本**: 3.8+ (推荐 3.9+)
- **内存**: 最少 4GB RAM (推荐 8GB+)
- **存储**: 最少 2GB 可用空间

### 硬件要求
- **机械臂**: 大象机器人 MyCobot 280 Pi
- **摄像头**: USB摄像头或CSI摄像头
- **音频设备**: 麦克风和扬声器
- **GPIO支持**: 树莓派4B (用于吸泵控制)

## 🔧 安装步骤

### 1. 克隆/下载项目
```bash
# 如果使用Git
git clone <repository_url>
cd embodied_agent_framework

# 或直接下载并解压项目文件
```

### 2. 安装Python依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 如果在树莓派上，额外安装GPIO支持
sudo apt-get install python3-rpi.gpio

# 如果需要机械臂支持
pip install pymycobot
```

### 3. 硬件连接
- 连接机械臂到电脑USB端口
- 连接摄像头
- 连接麦克风和扬声器
- 如果使用吸泵，连接GPIO控制电路

## ⚙️ 配置设置

### 方法一：使用配置助手（推荐）
```bash
python quick_start.py
# 选择: 1. 配置设置助手
```

### 方法二：手动配置

#### 1. 创建配置文件
```bash
python setup_config.py
```

#### 2. 设置环境变量
创建 `config/.env` 文件并填入以下内容：

```bash
# 私有化模型配置（必需）
PRIVATE_API_KEY=your_private_api_key_here
PRIVATE_BASE_URL=http://localhost:8000/v1
PRIVATE_LLM_MODEL=your_text_model_name
PRIVATE_VLM_MODEL=your_vision_model_name

# 在线模型API（可选）
YI_KEY=your_yi_api_key_here
QWEN_KEY=your_qwen_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
APPBUILDER_TOKEN=your_appbuilder_token_here

# 硬件配置
ROBOT_PORT=/dev/ttyUSB0

# 开发设置
DEBUG=false
LOG_LEVEL=INFO
```

#### 3. 调整硬件配置
编辑 `config/hardware.yaml`:

```yaml
robot:
  type: mycobot
  port: ${ROBOT_PORT:/dev/ttyUSB0}
  baudrate: 115200
  simulation_mode: false

camera:
  camera_index: 0  # 调整摄像头索引
  resolution: [640, 480]
  fps: 30

audio:
  input_device_index: null   # 设置麦克风设备号
  output_device_index: null  # 设置扬声器设备号
  sample_rate: 16000
```

## 🧪 测试验证

### 完整系统测试
```bash
python tests/test_system.py
```

### 分模块测试
```bash
# 测试AI模型连通性
python tests/test_models.py

# 测试硬件设备
python tests/test_hardware.py
```

### 使用快速启动脚本测试
```bash
python quick_start.py
# 选择相应的测试选项
```

## 📖 使用示例

### 1. 基础机械臂控制
```python
import asyncio
from embodied_agent import RobotController
from embodied_agent.hardware.mycobot import MyCobotAdapter
from embodied_agent.utils.config import ConfigManager

async def main():
    # 加载配置
    config_manager = ConfigManager()
    robot_config = config_manager.get_robot_config()

    # 创建机械臂适配器和控制器
    adapter = MyCobotAdapter(robot_config)
    robot = RobotController(adapter, robot_config)

    # 初始化
    await robot.initialize()

    # 基本动作
    await robot.move_to_home()  # 归零
    await robot.move_to_position(150, -120, 200)  # 移动到指定位置

    # 清理
    await robot.shutdown()

# 运行
asyncio.run(main())
```

### 2. 视觉处理
```python
import asyncio
from embodied_agent import VisionProcessor
from embodied_agent.utils.config import ConfigManager

async def main():
    # 加载配置
    config_manager = ConfigManager()
    camera_config = config_manager.get_camera_config()

    # 创建视觉处理器
    vision = VisionProcessor(camera_config)

    # 初始化
    await vision.initialize()

    # 拍照
    frame = await vision.capture_image('test_photo.jpg')

    # 物体检测
    color_ranges = {
        'red_block': {'lower': (0, 50, 50), 'upper': (10, 255, 255)},
        'green_block': {'lower': (50, 50, 50), 'upper': (70, 255, 255)}
    }
    detections = await vision.detect_objects_color(color_ranges)

    # 显示结果
    print(f"检测到 {len(detections.objects)} 个物体")
    for obj in detections.objects:
        print(f"- {obj.label}: 置信度 {obj.confidence:.2f}")

    # 清理
    await vision.shutdown()

asyncio.run(main())
```

### 3. 多模态融合
```python
import asyncio
from embodied_agent import MultiModalFusion, VisionProcessor, AudioProcessor
from embodied_agent.utils.config import ConfigManager

async def main():
    config_manager = ConfigManager()

    # 创建组件
    vision = VisionProcessor(config_manager.get_camera_config())
    audio = AudioProcessor(config_manager.get_audio_config())

    # 创建融合器
    fusion = MultiModalFusion({})
    fusion.set_vision_processor(vision)
    fusion.set_audio_processor(audio)

    # 初始化组件
    await vision.initialize()
    await audio.initialize()

    # 启动融合
    await fusion.start_fusion()

    # 运行一段时间
    await asyncio.sleep(10)

    # 获取场景上下文
    context = fusion.get_current_context()
    if context:
        print(f"场景描述: {context.scene_description}")
        print(f"检测到的物体: {context.detected_objects}")

    # 清理
    await fusion.stop_fusion()
    await vision.shutdown()
    await audio.shutdown()

asyncio.run(main())
```

## 🔍 故障排除

### 常见问题

#### 1. 机械臂连接失败
**错误**: `机械臂连接失败`

**解决方案**:
- 检查机械臂是否已开机
- 确认USB线连接正常
- 检查串口权限: `sudo chmod 666 /dev/ttyUSB0`
- 确认串口地址: `ls /dev/tty*`

#### 2. 摄像头无法打开
**错误**: `Failed to open camera`

**解决方案**:
- 检查摄像头是否被其他程序占用
- 尝试不同的摄像头索引 (0, 1, 2...)
- 检查摄像头权限
- 在Linux上尝试: `sudo usermod -a -G video $USER`

#### 3. API调用失败
**错误**: `API key not found` 或连接超时

**解决方案**:
- 确认API密钥正确设置
- 检查网络连接
- 确认私有模型服务正在运行
- 检查防火墙和代理设置

#### 4. 音频设备问题
**错误**: 录音或播放失败

**解决方案**:
- 检查音频设备连接
- 确认设备索引号正确
- 检查音频权限
- 运行 `python tests/test_hardware.py` 查看可用设备

#### 5. GPIO权限问题（树莓派）
**错误**: `Permission denied` for GPIO

**解决方案**:
- 使用sudo运行: `sudo python your_script.py`
- 添加用户到gpio组: `sudo usermod -a -G gpio $USER`
- 重启后重试

### 获取详细日志
```python
# 在代码开头添加日志配置
from loguru import logger
logger.add("debug.log", level="DEBUG")
```

### 检查配置状态
```bash
python quick_start.py
# 选择: 2. 查看当前配置
```

## 📞 技术支持

如果遇到无法解决的问题，请：

1. 查看测试报告: `tests/test_report.txt`
2. 检查日志文件: `logs/` 目录
3. 确认硬件连接和API配置
4. 参考原项目 `agent_demo_20250328` 的工作示例

## 🔄 更新和维护

### 更新依赖
```bash
pip install -r requirements.txt --upgrade
```

### 重新配置
```bash
# 删除配置文件后重新配置
rm config/.env
python setup_config.py
```

### 清理临时文件
```bash
# 清理临时文件
rm -rf temp/* logs/* tests/test_*.txt
```

---

**恭喜！** 您现在已经成功配置了具身智能体框架。开始构建您的AI机械臂应用吧！ 🎉