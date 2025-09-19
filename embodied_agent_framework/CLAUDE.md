# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 核心开发命令

### 快速启动和配置
```bash
# 启动项目主菜单（推荐入口）
python quick_start.py

# 配置设置助手（首次使用必需）
python setup_config.py

# 安装依赖
pip install -r requirements.txt
```

### 测试命令
```bash
# 完整系统测试（推荐）
python tests/test_system.py

# AI模型连通性测试
python tests/test_models.py

# 硬件设备功能测试
python tests/test_hardware.py

# 运行单个测试
pytest tests/test_system.py::TestSystemIntegration::test_basic_robot_control
```

### 代码质量
```bash
# 代码格式化
black embodied_agent/
isort embodied_agent/

# 代码检查
flake8 embodied_agent/
mypy embodied_agent/
```

## 系统架构概览

### 分层架构设计
本项目采用5层架构，从底层到顶层：

1. **硬件层** (`embodied_agent/hardware/`) - 物理设备适配器
2. **核心组件层** (`embodied_agent/core/`) - 基础功能模块
3. **接口层** (`embodied_agent/interfaces/`) - 抽象接口定义
4. **智能体层** (`embodied_agent/agents/`) - 高级编排逻辑（开发中）
5. **应用层** (`apps/`) - 具体应用实现（待开发）

### 关键架构特点

**异步编程模式**: 所有核心组件使用 `async/await` 模式，确保非阻塞操作。在修改或扩展时，保持异步模式一致性。

**接口驱动设计**:
- LLM/VLM模型通过 `LLMInterface` 和 `VLMInterface` 抽象
- 机械臂硬件通过 `RobotHardwareInterface` 抽象
- 添加新模型或硬件时，继承对应接口类

**配置管理**:
- 环境变量通过 `config/.env` 文件管理
- 配置类在 `embodied_agent/utils/config.py` 中定义
- 使用 `ConfigManager` 类获取所有配置

**模型集成现状**: 目前仅实现OpenAI兼容模型（`OpenAILLM`, `OpenAIVLM`），支持官方API和自部署服务。

## 重要实现细节

### 坐标转换系统
视觉系统和机械臂坐标转换通过 `embodied_agent/utils/calibration.py` 实现：
- 图像像素坐标 → 机械臂工作坐标
- 支持手眼标定和自动标定
- 修改视觉相关功能时必须考虑坐标转换

### 多模态融合
`embodied_agent/core/multimodal.py` 负责：
- 视觉、音频、机器人状态信息融合
- 统一的感知状态表示
- 为上层智能体提供整合的环境信息

### 硬件安全机制
机械臂控制包含多层安全检查：
- 工作空间边界检查（`motion_planning.py`）
- 运动轨迹规划和碰撞预测
- 紧急停止和状态监控

### 配置优先级
配置加载优先级（高到低）：
1. 函数参数直接传入
2. 环境变量
3. 配置文件 `config/.env`
4. 默认值

## 开发约定

### 语言和文档规范
**中文优先**: 本项目的注释、README、文档等均使用中文编写。这是项目的既定规范：
- 代码注释使用中文
- 变量名、函数名使用英文（遵循Python规范）
- 文档文件（README.md、配置指南等）使用中文
- commit信息使用中文
- 错误信息和日志输出使用中文

添加新功能时请保持这一约定，确保项目文档的一致性。

### 错误处理模式
- 硬件操作失败时优雅降级到仿真模式
- API调用使用指数退避重试机制
- 所有异常都应记录详细日志（使用loguru）

### 模型扩展指南
添加新AI模型时：
1. 在 `embodied_agent/models/` 下创建对应子目录
2. 继承 `LLMInterface` 或 `VLMInterface`
3. 实现所有抽象方法，特别是 `test_connection()`
4. 更新 `__init__.py` 文件的导出列表

### 硬件扩展指南
添加新硬件支持时：
1. 在 `embodied_agent/hardware/` 下创建适配器
2. 继承 `RobotHardwareInterface`
3. 实现安全检查和状态监控
4. 添加对应的测试用例

### 状态管理注意事项
- 机械臂状态通过 `RobotState` 枚举管理
- 多模态状态通过 `MultiModalState` 统一表示
- 避免直接修改共享状态，使用深拷贝

## 当前开发重点

根据TODO列表，当前优先级：
1. **智能体编排引擎** - 实现任务规划和技能组合
2. **AI学伴应用** - 基于现有框架构建教育应用
3. **系统集成测试** - 完善端到端测试覆盖

注意：`embodied_agent/agents/` 目录下的组件（EmbodiedAgent, TaskPlanner, SkillLibrary）在主__init__.py中被导出，但实际文件尚未实现。在使用这些组件前需要先实现对应模块。