"""
Core components for the Embodied Agent Framework
"""

from .robot import RobotController
from .vision import VisionProcessor
from .audio import AudioProcessor
from .multimodal import MultiModalFusion

__all__ = [
    "RobotController",
    "VisionProcessor",
    "AudioProcessor",
    "MultiModalFusion",
]