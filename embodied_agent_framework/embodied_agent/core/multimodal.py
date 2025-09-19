"""
Multimodal Fusion Module - Integrates vision, audio, and robot state information
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from loguru import logger
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum

from .vision import VisionProcessor, DetectionResult
from .audio import AudioProcessor
from .robot import RobotController
from ..interfaces.robot_hardware import CartesianPosition


class ModalityType(Enum):
    """Available modality types"""
    VISION = "vision"
    AUDIO = "audio"
    ROBOT_STATE = "robot_state"
    TEXT = "text"


@dataclass
class MultiModalInput:
    """Multimodal input data structure"""
    timestamp: float
    modality: ModalityType
    data: Any
    metadata: Dict[str, Any]


class SceneContext(BaseModel):
    """Scene context information"""
    detected_objects: List[str]
    robot_position: Optional[CartesianPosition]
    audio_activity: bool
    scene_description: str = ""
    confidence: float = 0.0
    timestamp: float


class MultiModalFusion:
    """
    Multimodal fusion engine that combines information from multiple sensors
    and modalities to create a comprehensive understanding of the scene
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize multimodal fusion

        Args:
            config: Fusion configuration
        """
        self.config = config

        # Components
        self.vision_processor: Optional[VisionProcessor] = None
        self.audio_processor: Optional[AudioProcessor] = None
        self.robot_controller: Optional[RobotController] = None

        # Fusion parameters
        self.context_window = config.get('context_window', 5.0)  # seconds
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.fusion_frequency = config.get('fusion_frequency', 10.0)  # Hz

        # State tracking
        self.scene_history: List[SceneContext] = []
        self.current_context: Optional[SceneContext] = None
        self._fusion_active = False

        # Object tracking
        self.tracked_objects: Dict[str, Dict[str, Any]] = {}
        self.object_persistence_time = config.get('object_persistence_time', 3.0)

        # Color detection settings for objects
        self.color_ranges = config.get('color_ranges', {
            'red_object': {
                'lower': (0, 50, 50),
                'upper': (10, 255, 255)
            },
            'green_object': {
                'lower': (50, 50, 50),
                'upper': (70, 255, 255)
            },
            'blue_object': {
                'lower': (100, 50, 50),
                'upper': (120, 255, 255)
            }
        })

    def set_vision_processor(self, vision_processor: VisionProcessor):
        """Set vision processor component"""
        self.vision_processor = vision_processor
        logger.info("Vision processor connected to multimodal fusion")

    def set_audio_processor(self, audio_processor: AudioProcessor):
        """Set audio processor component"""
        self.audio_processor = audio_processor
        logger.info("Audio processor connected to multimodal fusion")

    def set_robot_controller(self, robot_controller: RobotController):
        """Set robot controller component"""
        self.robot_controller = robot_controller
        logger.info("Robot controller connected to multimodal fusion")

    async def start_fusion(self) -> bool:
        """
        Start multimodal fusion process

        Returns:
            bool: True if fusion started successfully
        """
        try:
            if self._fusion_active:
                logger.warning("Fusion already active")
                return True

            self._fusion_active = True

            # Start fusion loop
            asyncio.create_task(self._fusion_loop())

            logger.info("Multimodal fusion started")
            return True

        except Exception as e:
            logger.error(f"Error starting fusion: {e}")
            return False

    async def stop_fusion(self) -> bool:
        """
        Stop multimodal fusion process

        Returns:
            bool: True if fusion stopped successfully
        """
        try:
            self._fusion_active = False
            logger.info("Multimodal fusion stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping fusion: {e}")
            return False

    async def _fusion_loop(self):
        """Main fusion processing loop"""
        try:
            while self._fusion_active:
                # Collect data from all modalities
                vision_data = await self._collect_vision_data()
                audio_data = await self._collect_audio_data()
                robot_data = await self._collect_robot_data()

                # Fuse multimodal data
                context = await self._fuse_modalities(vision_data, audio_data, robot_data)

                if context:
                    self.current_context = context
                    self._update_scene_history(context)

                # Control fusion frequency
                await asyncio.sleep(1.0 / self.fusion_frequency)

        except Exception as e:
            logger.error(f"Error in fusion loop: {e}")
        finally:
            self._fusion_active = False

    async def _collect_vision_data(self) -> Optional[MultiModalInput]:
        """Collect data from vision processor"""
        try:
            if not self.vision_processor:
                return None

            # Get current frame and detect objects
            frame = self.vision_processor.get_current_frame()
            if frame is None:
                return None

            # Detect objects using color-based detection
            detection_result = await self.vision_processor.detect_objects_color(self.color_ranges)

            return MultiModalInput(
                timestamp=time.time(),
                modality=ModalityType.VISION,
                data=detection_result,
                metadata={'frame_available': True}
            )

        except Exception as e:
            logger.error(f"Error collecting vision data: {e}")
            return None

    async def _collect_audio_data(self) -> Optional[MultiModalInput]:
        """Collect data from audio processor"""
        try:
            if not self.audio_processor:
                return None

            # For now, just report if audio processor is active
            # In a full implementation, this could include:
            # - Audio level detection
            # - Speech activity detection
            # - Sound classification

            return MultiModalInput(
                timestamp=time.time(),
                modality=ModalityType.AUDIO,
                data={'audio_available': True},
                metadata={'processor_active': True}
            )

        except Exception as e:
            logger.error(f"Error collecting audio data: {e}")
            return None

    async def _collect_robot_data(self) -> Optional[MultiModalInput]:
        """Collect data from robot controller"""
        try:
            if not self.robot_controller:
                return None

            # Get current robot position and state
            position = await self.robot_controller.get_current_position()
            state = await self.robot_controller.get_robot_state()

            return MultiModalInput(
                timestamp=time.time(),
                modality=ModalityType.ROBOT_STATE,
                data={
                    'position': position,
                    'state': state
                },
                metadata={'robot_connected': True}
            )

        except Exception as e:
            logger.error(f"Error collecting robot data: {e}")
            return None

    async def _fuse_modalities(self, vision_data: Optional[MultiModalInput],
                             audio_data: Optional[MultiModalInput],
                             robot_data: Optional[MultiModalInput]) -> Optional[SceneContext]:
        """
        Fuse data from multiple modalities into scene context

        Args:
            vision_data: Vision input data
            audio_data: Audio input data
            robot_data: Robot state data

        Returns:
            Optional[SceneContext]: Fused scene context
        """
        try:
            current_time = time.time()
            detected_objects = []
            robot_position = None
            audio_activity = False
            confidence = 0.0

            # Process vision data
            if vision_data and vision_data.modality == ModalityType.VISION:
                detection_result: DetectionResult = vision_data.data
                detected_objects = [obj.label for obj in detection_result.objects]

                # Update object tracking
                self._update_object_tracking(detection_result, current_time)

                if detected_objects:
                    confidence += 0.4  # Vision contributes 40% to confidence

            # Process robot data
            if robot_data and robot_data.modality == ModalityType.ROBOT_STATE:
                robot_position = robot_data.data.get('position')
                if robot_position:
                    confidence += 0.3  # Robot state contributes 30% to confidence

            # Process audio data
            if audio_data and audio_data.modality == ModalityType.AUDIO:
                audio_activity = audio_data.data.get('audio_available', False)
                if audio_activity:
                    confidence += 0.3  # Audio contributes 30% to confidence

            # Generate scene description
            scene_description = self._generate_scene_description(
                detected_objects, robot_position, audio_activity
            )

            return SceneContext(
                detected_objects=detected_objects,
                robot_position=robot_position,
                audio_activity=audio_activity,
                scene_description=scene_description,
                confidence=confidence,
                timestamp=current_time
            )

        except Exception as e:
            logger.error(f"Error fusing modalities: {e}")
            return None

    def _update_object_tracking(self, detection_result: DetectionResult, current_time: float):
        """
        Update object tracking with new detections

        Args:
            detection_result: Latest detection results
            current_time: Current timestamp
        """
        try:
            # Update existing objects and add new ones
            detected_labels = set()

            for obj in detection_result.objects:
                detected_labels.add(obj.label)

                if obj.label in self.tracked_objects:
                    # Update existing object
                    self.tracked_objects[obj.label].update({
                        'last_seen': current_time,
                        'position': (obj.x1, obj.y1, obj.x2, obj.y2),
                        'confidence': obj.confidence,
                        'detections': self.tracked_objects[obj.label]['detections'] + 1
                    })
                else:
                    # Add new object
                    self.tracked_objects[obj.label] = {
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'position': (obj.x1, obj.y1, obj.x2, obj.y2),
                        'confidence': obj.confidence,
                        'detections': 1
                    }

            # Remove objects that haven't been seen recently
            objects_to_remove = []
            for label, obj_data in self.tracked_objects.items():
                if (current_time - obj_data['last_seen']) > self.object_persistence_time:
                    objects_to_remove.append(label)

            for label in objects_to_remove:
                del self.tracked_objects[label]
                logger.debug(f"Removed object from tracking: {label}")

        except Exception as e:
            logger.error(f"Error updating object tracking: {e}")

    def _generate_scene_description(self, detected_objects: List[str],
                                  robot_position: Optional[CartesianPosition],
                                  audio_activity: bool) -> str:
        """
        Generate natural language scene description

        Args:
            detected_objects: List of detected object labels
            robot_position: Robot position
            audio_activity: Audio activity status

        Returns:
            str: Scene description
        """
        try:
            description_parts = []

            # Describe detected objects
            if detected_objects:
                if len(detected_objects) == 1:
                    description_parts.append(f"I can see a {detected_objects[0]}")
                else:
                    objects_str = ", ".join(detected_objects[:-1])
                    description_parts.append(f"I can see {objects_str} and {detected_objects[-1]}")
            else:
                description_parts.append("I don't see any specific objects")

            # Describe robot state
            if robot_position:
                description_parts.append(f"Robot is at position ({robot_position.x:.0f}, "
                                       f"{robot_position.y:.0f}, {robot_position.z:.0f})")

            # Describe audio activity
            if audio_activity:
                description_parts.append("Audio system is active")

            return ". ".join(description_parts) + "."

        except Exception as e:
            logger.error(f"Error generating scene description: {e}")
            return "Scene analysis unavailable"

    def _update_scene_history(self, context: SceneContext):
        """
        Update scene history with new context

        Args:
            context: New scene context
        """
        try:
            self.scene_history.append(context)

            # Remove old contexts outside the window
            cutoff_time = context.timestamp - self.context_window
            self.scene_history = [
                ctx for ctx in self.scene_history
                if ctx.timestamp > cutoff_time
            ]

        except Exception as e:
            logger.error(f"Error updating scene history: {e}")

    def get_current_context(self) -> Optional[SceneContext]:
        """
        Get current scene context

        Returns:
            Optional[SceneContext]: Current scene context
        """
        return self.current_context

    def get_scene_history(self, duration: float = None) -> List[SceneContext]:
        """
        Get scene history

        Args:
            duration: Time window in seconds (None for all history)

        Returns:
            List[SceneContext]: Scene history
        """
        if duration is None:
            return self.scene_history.copy()

        cutoff_time = time.time() - duration
        return [ctx for ctx in self.scene_history if ctx.timestamp > cutoff_time]

    def get_tracked_objects(self) -> Dict[str, Dict[str, Any]]:
        """
        Get currently tracked objects

        Returns:
            Dict[str, Dict[str, Any]]: Tracked objects information
        """
        return self.tracked_objects.copy()

    def find_object_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """
        Find tracked object by label

        Args:
            label: Object label to find

        Returns:
            Optional[Dict[str, Any]]: Object information or None if not found
        """
        return self.tracked_objects.get(label)

    def get_objects_in_scene(self) -> List[str]:
        """
        Get list of objects currently in scene

        Returns:
            List[str]: Object labels
        """
        if self.current_context:
            return self.current_context.detected_objects
        return []

    def is_object_present(self, label: str) -> bool:
        """
        Check if specific object is present in current scene

        Args:
            label: Object label to check

        Returns:
            bool: True if object is present
        """
        return label in self.get_objects_in_scene()

    async def wait_for_object(self, label: str, timeout: float = 10.0) -> bool:
        """
        Wait for specific object to appear in scene

        Args:
            label: Object label to wait for
            timeout: Maximum wait time in seconds

        Returns:
            bool: True if object appeared, False if timeout
        """
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if self.is_object_present(label):
                return True
            await asyncio.sleep(0.1)

        return False