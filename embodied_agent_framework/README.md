# 🤖 具身智能体框架 (Embodied Agent Framework)

一个标准化、模块化的具身AI智能体开发框架，整合了机械臂控制、多模态感知和大语言模型。

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 核心特性

- **🔧 模块化架构**: 清晰的组件分离，支持插拔式扩展
- **🤖 机器人无关**: 标准化接口支持多种机械臂 (MyCobot, UR等)
- **🧠 大模型集成**: 支持OpenAI、Claude、私有化部署等多种LLM
- **👁️ 多模态感知**: 视觉、音频、触觉等多种传感器融合
- **⚡ 实时处理**: 异步架构确保响应性交互
- **📚 技能库**: 可扩展的预构建操作技能集
- **🎓 AI学伴**: 内置的教育辅助应用

## 🏗️ 系统架构

```
📦 具身智能体框架
├── 🎯 应用层 (Application Layer)
│   ├── AI学伴 - 学习辅助应用
│   ├── 工业助手 - 工业自动化应用
│   └── 自定义应用 - 用户扩展应用
├── 🧠 智能体层 (Agent Layer)
│   ├── 任务规划器 - Task Planner
│   ├── 技能编排器 - Skills Orchestrator
│   └── 上下文管理器 - Context Manager
├── 🔌 接口层 (Interface Layer)
│   ├── LLM接口 - 大语言模型接口
│   ├── VLM接口 - 视觉语言模型接口
│   └── 硬件接口 - 机器人硬件抽象接口
├── 🎪 核心组件层 (Core Components)
│   ├── 机械臂控制器 - Robot Controller
│   ├── 视觉处理器 - Vision Processor
│   ├── 音频处理器 - Audio Processor
│   └── 多模态融合器 - Multi-modal Fusion
└── 🔧 硬件层 (Hardware Layer)
    ├── 机械臂硬件 - MyCobot等
    ├── 摄像头设备 - USB/CSI摄像头
    └── 音频设备 - 麦克风/扬声器
```

## 🚀 快速开始

### 一键启动
```bash
# 进入项目目录
cd embodied_agent_framework

# 运行快速启动脚本
python quick_start.py
```

### 配置设置
1. 在快速启动菜单中选择 "配置设置助手"
2. 按照提示输入API密钥和硬件配置
3. 运行系统测试验证配置

### 详细安装步骤
参见 **[📖 详细配置指南](SETUP_GUIDE.md)**

## 🎓 应用示例

### AI学伴 (AI Tutor)
智能学习辅助系统，通过视觉理解和物理交互帮助学生完成作业。

**主要功能:**
- 📝 作业视觉分析
- 🔍 逐步问题解决
- 🤝 交互式演示
- 📊 学习进度跟踪

### 基础使用示例
```python
import asyncio
from embodied_agent import RobotController, VisionProcessor
from embodied_agent.hardware.mycobot import MyCobotAdapter
from embodied_agent.utils.config import ConfigManager

async def main():
    # 加载配置
    config_manager = ConfigManager()
    robot_config = config_manager.get_robot_config()

    # 创建机械臂控制器
    adapter = MyCobotAdapter(robot_config)
    robot = RobotController(adapter, robot_config)

    # 初始化并执行基本动作
    await robot.initialize()
    await robot.move_to_home()  # 归零
    await robot.move_to_position(150, -120, 200)  # 移动到指定位置
    await robot.shutdown()

asyncio.run(main())
```

## 🔧 支持的硬件

### 机械臂
- ✅ **大象机器人 MyCobot 280** - 完全支持
- 🔄 **Universal Robots** - 计划支持
- 🔄 **KUKA** - 计划支持

### 传感器
- ✅ **USB/CSI摄像头** - 完全支持
- ✅ **麦克风/扬声器** - 完全支持
- 🔄 **RGB-D摄像头** - 计划支持

### 支持的AI模型
- ✅ **私有化部署** - OpenAI格式API
- ✅ **零一万物** - Yi-Large, Yi-Vision
- ✅ **通义千问** - Qwen-VL-Max
- ✅ **百度AppBuilder** - TTS/ASR
- 🔄 **Claude** - 计划支持

## 📋 开发状态跟踪

### ✅ 已完成的功能

#### 🏗️ 核心架构
- ✅ **项目结构设计** - 模块化目录结构
- ✅ **接口抽象层** - LLM/VLM/硬件接口定义
- ✅ **配置管理系统** - 统一配置文件和环境变量管理

#### 🤖 硬件控制层
- ✅ **机械臂硬件接口** - 抽象基类定义
- ✅ **MyCobot适配器** - 大象机器人MyCobot 280支持
- ✅ **运动规划** - 安全轨迹规划和碰撞检测
- ✅ **手眼标定** - 图像坐标与机械臂坐标转换

#### 👁️ 感知处理层
- ✅ **视觉处理器** - 摄像头控制、图像处理、物体检测
- ✅ **音频处理器** - 录音、播放、语音激活检测
- ✅ **多模态融合** - 视觉、音频、机器人状态融合

#### 🧠 AI模型接口
- ✅ **LLM接口抽象** - 大语言模型统一接口
- ✅ **VLM接口抽象** - 视觉语言模型统一接口
- ✅ **OpenAI格式支持** - 兼容OpenAI API格式

#### 🛠️ 开发工具
- ✅ **配置设置助手** - 交互式配置工具
- ✅ **快速启动脚本** - 一键启动和菜单系统
- ✅ **完整测试套件** - 系统、模型、硬件测试
- ✅ **详细文档** - 配置指南和API文档

### 🔄 开发中的功能

#### 🧠 智能体编排层
- 🔄 **任务规划器** - 高级任务分解和规划
- 🔄 **技能编排器** - 基础技能组合和执行
- 🔄 **上下文管理器** - 对话历史和场景记忆
- 🔄 **决策引擎** - 基于多模态信息的决策

#### 🔌 模型实现
- 🔄 **OpenAI模型实现** - GPT-4等模型的具体实现
- 🔄 **Claude模型实现** - Claude系列模型集成
- 🔄 **零一万物实现** - Yi-Large/Yi-Vision实现类
- 🔄 **通义千问实现** - Qwen-VL-Max实现类

### ❌ 待开发的功能

#### 🎓 应用层
- ❌ **AI学伴应用** - 学习辅助智能体
- ❌ **工业助手应用** - 工业自动化应用
- ❌ **演示应用** - 基础功能演示

#### 📚 技能库
- ❌ **基础操作技能** - 抓取、放置、推拉等
- ❌ **复杂任务技能** - 装配、分拣、清理等
- ❌ **学习任务技能** - 指向、演示、问答等

#### 🔧 硬件扩展
- ❌ **UR机械臂支持** - Universal Robots适配器
- ❌ **KUKA机械臂支持** - KUKA机械臂适配器
- ❌ **RGB-D摄像头** - 深度摄像头支持
- ❌ **力觉传感器** - 触觉反馈支持

#### 🌐 高级功能
- ❌ **远程控制** - Web界面和API服务
- ❌ **数据记录** - 操作历史和性能分析
- ❌ **在线学习** - 强化学习和适应性改进
- ❌ **多机器人协作** - 多智能体协调

### 🎯 近期开发计划

1. **第一阶段** (当前)
   - 🔄 完善智能体编排引擎
   - 🔄 实现具体的LLM/VLM模型类
   - 🔄 开发AI学伴应用原型

2. **第二阶段** (下一步)
   - ❌ 构建基础技能库
   - ❌ 添加更多硬件支持
   - ❌ 开发Web管理界面

3. **第三阶段** (未来)
   - ❌ 实现高级AI功能
   - ❌ 支持多机器人协作
   - ❌ 商业化应用开发

## 🧪 测试验证

### 完整系统测试
```bash
python tests/test_system.py    # 完整系统功能测试
python tests/test_models.py    # AI模型连通性测试
python tests/test_hardware.py  # 硬件设备功能测试
```

### 或使用快速启动脚本
```bash
python quick_start.py
# 选择相应的测试选项
```

## 📚 文档资源

- **[📖 详细配置指南](SETUP_GUIDE.md)** - 完整的安装和配置说明
- **[🔧 API参考](docs/api.md)** - 详细的API文档
- **[⚙️ 硬件设置](docs/hardware.md)** - 硬件连接指南
- **[🎯 应用开发](docs/applications.md)** - 自定义应用开发
- **[🤝 贡献指南](docs/contributing.md)** - 参与项目开发

## 🛠️ 项目结构

```
embodied_agent_framework/
├── embodied_agent/              # 🎯 核心框架库
│   ├── core/                    # 核心组件
│   ├── interfaces/              # 接口抽象层
│   ├── hardware/                # 硬件适配器
│   ├── agents/                  # 智能体编排
│   └── utils/                   # 工具模块
├── apps/                        # 🎓 应用层
│   └── ai_tutor/               # AI学伴应用
├── tests/                       # 🧪 测试代码
├── config/                      # ⚙️ 配置文件
├── quick_start.py              # 🚀 快速启动脚本
├── setup_config.py             # 🔧 配置设置助手
└── SETUP_GUIDE.md              # 📖 详细配置指南
```

## 🤝 参与贡献

我们欢迎各种形式的贡献！请查看 [贡献指南](docs/contributing.md) 了解详情。

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 基于同济子豪兄的开创性工作
- 感谢具身AI研究社区的启发
- 特别感谢大象机器人的硬件支持

---

**🎉 开始您的具身AI之旅！**

如有问题，请查看 [配置指南](SETUP_GUIDE.md) 或运行 `python quick_start.py` 获取帮助。