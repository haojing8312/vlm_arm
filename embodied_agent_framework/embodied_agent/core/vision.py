"""
Vision Processing Module - Handles camera input and computer vision tasks
"""

import asyncio
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import time
from loguru import logger
from pydantic import BaseModel

from ..utils.config import ConfigManager


class BoundingBox(BaseModel):
    """Bounding box representation"""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float = 1.0
    label: str = ""


class DetectionResult(BaseModel):
    """Object detection result"""
    objects: List[BoundingBox]
    image_width: int
    image_height: int
    timestamp: float


class VisionProcessor:
    """
    Vision processor for camera input, image processing, and computer vision tasks
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize vision processor

        Args:
            config: Vision processing configuration
        """
        self.config = config

        # Camera configuration
        self.camera_index = config.get('camera_index', 0)
        self.resolution = config.get('resolution', (640, 480))
        self.fps = config.get('fps', 30)

        # Image processing parameters
        self.auto_exposure = config.get('auto_exposure', True)
        self.brightness = config.get('brightness', 0)
        self.contrast = config.get('contrast', 1.0)

        # Storage settings
        self.save_directory = config.get('save_directory', 'temp')
        self.image_format = config.get('image_format', 'jpg')

        # Camera instance
        self._camera: Optional[cv2.VideoCapture] = None
        self._is_streaming = False
        self._current_frame: Optional[np.ndarray] = None

        # Calibration and enhancement
        self._camera_matrix: Optional[np.ndarray] = None
        self._distortion_coeffs: Optional[np.ndarray] = None

    async def initialize(self) -> bool:
        """
        Initialize vision processor and camera

        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize camera
            self._camera = cv2.VideoCapture(self.camera_index)

            if not self._camera.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False

            # Configure camera
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self._camera.set(cv2.CAP_PROP_FPS, self.fps)

            if not self.auto_exposure:
                self._camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)

            # Test camera
            ret, frame = self._camera.read()
            if not ret:
                logger.error("Failed to read from camera")
                return False

            self._current_frame = frame
            logger.info(f"Vision processor initialized with camera {self.camera_index}")
            logger.info(f"Camera resolution: {frame.shape[1]}x{frame.shape[0]}")

            return True

        except Exception as e:
            logger.error(f"Error initializing vision processor: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        Shutdown vision processor

        Returns:
            bool: True if shutdown successful
        """
        try:
            await self.stop_streaming()

            if self._camera:
                self._camera.release()
                self._camera = None

            cv2.destroyAllWindows()
            logger.info("Vision processor shutdown complete")
            return True

        except Exception as e:
            logger.error(f"Error during vision processor shutdown: {e}")
            return False

    async def capture_image(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Capture a single image from camera

        Args:
            save_path: Optional path to save the image

        Returns:
            Optional[np.ndarray]: Captured image or None if failed
        """
        try:
            if not self._camera or not self._camera.isOpened():
                logger.error("Camera not initialized")
                return None

            # Capture frame
            ret, frame = self._camera.read()
            if not ret:
                logger.error("Failed to capture image")
                return None

            # Apply image enhancements
            frame = self._enhance_image(frame)

            # Save image if path provided
            if save_path:
                cv2.imwrite(save_path, frame)
                logger.info(f"Image saved to {save_path}")

            self._current_frame = frame
            return frame

        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None

    async def start_streaming(self, display: bool = False) -> bool:
        """
        Start camera streaming

        Args:
            display: Whether to display the video stream

        Returns:
            bool: True if streaming started successfully
        """
        try:
            if self._is_streaming:
                logger.warning("Streaming already active")
                return True

            self._is_streaming = True

            # Start streaming task
            asyncio.create_task(self._streaming_loop(display))

            logger.info("Camera streaming started")
            return True

        except Exception as e:
            logger.error(f"Error starting streaming: {e}")
            return False

    async def stop_streaming(self) -> bool:
        """
        Stop camera streaming

        Returns:
            bool: True if streaming stopped successfully
        """
        try:
            self._is_streaming = False
            cv2.destroyAllWindows()
            logger.info("Camera streaming stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping streaming: {e}")
            return False

    async def _streaming_loop(self, display: bool = False):
        """
        Main streaming loop

        Args:
            display: Whether to display the video stream
        """
        try:
            while self._is_streaming and self._camera and self._camera.isOpened():
                ret, frame = self._camera.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    continue

                # Apply enhancements
                frame = self._enhance_image(frame)
                self._current_frame = frame

                # Display frame if requested
                if display:
                    cv2.imshow('EmbodiedAgent Camera', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Control frame rate
                await asyncio.sleep(1.0 / self.fps)

        except Exception as e:
            logger.error(f"Error in streaming loop: {e}")
        finally:
            self._is_streaming = False

    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the current camera frame

        Returns:
            Optional[np.ndarray]: Current frame or None if not available
        """
        return self._current_frame.copy() if self._current_frame is not None else None

    async def detect_objects_color(self, color_ranges: Dict[str, Dict[str, Tuple[int, int, int]]]) -> DetectionResult:
        """
        Detect objects based on color ranges

        Args:
            color_ranges: Dictionary mapping object names to HSV color ranges
                         e.g., {'red_block': {'lower': (0, 50, 50), 'upper': (10, 255, 255)}}

        Returns:
            DetectionResult: Detection results
        """
        try:
            frame = self.get_current_frame()
            if frame is None:
                logger.error("No current frame available for detection")
                return DetectionResult(objects=[], image_width=0, image_height=0, timestamp=time.time())

            height, width = frame.shape[:2]
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            objects = []

            for object_name, color_range in color_ranges.items():
                lower = np.array(color_range['lower'])
                upper = np.array(color_range['upper'])

                # Create mask
                mask = cv2.inRange(hsv, lower, upper)

                # Morphological operations to reduce noise
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 500:  # Minimum area threshold
                        x, y, w, h = cv2.boundingRect(contour)
                        confidence = min(1.0, area / 10000)  # Simple confidence based on area

                        bbox = BoundingBox(
                            x1=x, y1=y, x2=x+w, y2=y+h,
                            confidence=confidence,
                            label=object_name
                        )
                        objects.append(bbox)

            return DetectionResult(
                objects=objects,
                image_width=width,
                image_height=height,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error in color-based object detection: {e}")
            return DetectionResult(objects=[], image_width=0, image_height=0, timestamp=time.time())

    def draw_detections(self, image: np.ndarray, detection_result: DetectionResult) -> np.ndarray:
        """
        Draw detection results on image

        Args:
            image: Input image
            detection_result: Detection results to draw

        Returns:
            np.ndarray: Image with drawn detections
        """
        try:
            result_image = image.copy()

            for obj in detection_result.objects:
                # Draw bounding box
                cv2.rectangle(result_image, (obj.x1, obj.y1), (obj.x2, obj.y2), (0, 255, 0), 2)

                # Draw label
                label_text = f"{obj.label}: {obj.confidence:.2f}"
                label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(result_image,
                            (obj.x1, obj.y1 - label_size[1] - 10),
                            (obj.x1 + label_size[0], obj.y1), (0, 255, 0), -1)
                cv2.putText(result_image, label_text, (obj.x1, obj.y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                # Draw center point
                center_x = (obj.x1 + obj.x2) // 2
                center_y = (obj.y1 + obj.y2) // 2
                cv2.circle(result_image, (center_x, center_y), 5, (255, 0, 0), -1)

            return result_image

        except Exception as e:
            logger.error(f"Error drawing detections: {e}")
            return image

    def get_object_center(self, bbox: BoundingBox) -> Tuple[int, int]:
        """
        Get center coordinates of bounding box

        Args:
            bbox: Bounding box

        Returns:
            Tuple[int, int]: Center coordinates (x, y)
        """
        center_x = (bbox.x1 + bbox.x2) // 2
        center_y = (bbox.y1 + bbox.y2) // 2
        return center_x, center_y

    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply image enhancements

        Args:
            image: Input image

        Returns:
            np.ndarray: Enhanced image
        """
        try:
            enhanced = image.copy()

            # Apply brightness adjustment
            if self.brightness != 0:
                enhanced = cv2.add(enhanced, np.ones(enhanced.shape, dtype=np.uint8) * self.brightness)

            # Apply contrast adjustment
            if self.contrast != 1.0:
                enhanced = cv2.convertScaleAbs(enhanced, alpha=self.contrast, beta=0)

            # Apply camera calibration if available
            if self._camera_matrix is not None and self._distortion_coeffs is not None:
                enhanced = cv2.undistort(enhanced, self._camera_matrix, self._distortion_coeffs)

            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image

    def save_current_frame(self, filename: Optional[str] = None) -> bool:
        """
        Save current frame to file

        Args:
            filename: Optional filename, if None generates timestamp-based name

        Returns:
            bool: True if save successful
        """
        try:
            frame = self.get_current_frame()
            if frame is None:
                logger.error("No current frame to save")
                return False

            if filename is None:
                timestamp = int(time.time())
                filename = f"capture_{timestamp}.{self.image_format}"

            filepath = f"{self.save_directory}/{filename}"

            # Ensure directory exists
            import os
            os.makedirs(self.save_directory, exist_ok=True)

            cv2.imwrite(filepath, frame)
            logger.info(f"Frame saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving frame: {e}")
            return False

    def load_camera_calibration(self, calibration_file: str) -> bool:
        """
        Load camera calibration parameters

        Args:
            calibration_file: Path to calibration file

        Returns:
            bool: True if calibration loaded successfully
        """
        try:
            import numpy as np
            calibration = np.load(calibration_file)
            self._camera_matrix = calibration['camera_matrix']
            self._distortion_coeffs = calibration['distortion_coefficients']
            logger.info(f"Camera calibration loaded from {calibration_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading camera calibration: {e}")
            return False