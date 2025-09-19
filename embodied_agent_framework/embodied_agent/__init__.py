"""
Embodied Agent Framework

A standardized framework for building embodied AI agents with robotic arms,
multi-modal sensing, and large language model integration.
"""

__version__ = "0.1.0"
__author__ = "EmbodiedAI Team"
__email__ = "contact@embodiedai.dev"

from .core import (
    RobotController,
    VisionProcessor,
    AudioProcessor,
    MultiModalFusion,
)

from .interfaces import (
    LLMInterface,
    VLMInterface,
    RobotHardwareInterface,
)

from .agents import (
    EmbodiedAgent,
    SkillLibrary,
    TaskPlanner,
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "RobotController",
    "VisionProcessor",
    "AudioProcessor",
    "MultiModalFusion",
    "LLMInterface",
    "VLMInterface",
    "RobotHardwareInterface",
    "EmbodiedAgent",
    "SkillLibrary",
    "TaskPlanner",
]