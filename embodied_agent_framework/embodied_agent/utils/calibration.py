"""
Hand-Eye Calibration utilities for converting between image and robot coordinates
"""

import json
import os
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from loguru import logger


class HandEyeCalibration:
    """
    Hand-eye calibration for converting between image pixel coordinates
    and robot world coordinates.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize hand-eye calibration

        Args:
            config: Calibration configuration
        """
        self.config = config
        self.calibration_file = config.get('calibration_file', 'config/hand_eye_calibration.json')

        # Calibration parameters
        self.image_points: List[Tuple[int, int]] = []
        self.robot_points: List[Tuple[float, float]] = []
        self.transform_matrix: Optional[np.ndarray] = None
        self.is_calibrated = False

        # Default calibration points (can be overridden)
        self.default_image_points = [
            (130, 290),  # Bottom-left calibration point
            (640, 0),    # Top-right calibration point
        ]
        self.default_robot_points = [
            (-21.8, -197.4),  # Bottom-left robot coordinate
            (215, -59.1),     # Top-right robot coordinate
        ]

    def calibrate(self, image_points: List[Tuple[int, int]],
                  robot_points: List[Tuple[float, float]]) -> bool:
        """
        Perform hand-eye calibration using provided calibration points

        Args:
            image_points: List of pixel coordinates [(x, y), ...]
            robot_points: List of corresponding robot coordinates [(x, y), ...]

        Returns:
            bool: True if calibration successful
        """
        try:
            if len(image_points) != len(robot_points) or len(image_points) < 2:
                logger.error("Need at least 2 corresponding calibration points")
                return False

            self.image_points = image_points
            self.robot_points = robot_points

            # For 2-point calibration, use linear interpolation
            if len(image_points) == 2:
                self._calibrate_2_point()
            else:
                # For more points, use least squares fitting
                self._calibrate_multi_point()

            self.is_calibrated = True
            self.save_calibration()
            logger.info(f"Hand-eye calibration completed with {len(image_points)} points")
            return True

        except Exception as e:
            logger.error(f"Error during calibration: {e}")
            return False

    def _calibrate_2_point(self):
        """Perform 2-point linear calibration"""
        img_p1, img_p2 = self.image_points
        rob_p1, rob_p2 = self.robot_points

        # Calculate scale and offset for X and Y
        self.x_scale = (rob_p2[0] - rob_p1[0]) / (img_p2[0] - img_p1[0])
        self.x_offset = rob_p1[0] - self.x_scale * img_p1[0]

        self.y_scale = (rob_p2[1] - rob_p1[1]) / (img_p2[1] - img_p1[1])
        self.y_offset = rob_p1[1] - self.y_scale * img_p1[1]

        logger.info(f"2-point calibration: X scale={self.x_scale:.3f}, offset={self.x_offset:.3f}")
        logger.info(f"2-point calibration: Y scale={self.y_scale:.3f}, offset={self.y_offset:.3f}")

    def _calibrate_multi_point(self):
        """Perform multi-point calibration using least squares"""
        img_points = np.array(self.image_points, dtype=np.float32)
        rob_points = np.array(self.robot_points, dtype=np.float32)

        # Prepare matrices for least squares: [x, y, 1] -> [rob_x, rob_y]
        A = np.column_stack([img_points, np.ones(len(img_points))])

        # Solve for transformation parameters
        transform_x = np.linalg.lstsq(A, rob_points[:, 0], rcond=None)[0]
        transform_y = np.linalg.lstsq(A, rob_points[:, 1], rcond=None)[0]

        self.transform_matrix = np.array([transform_x, transform_y])
        logger.info(f"Multi-point calibration completed with transform matrix:\n{self.transform_matrix}")

    def image_to_robot(self, image_x: int, image_y: int) -> Optional[Tuple[float, float]]:
        """
        Convert image coordinates to robot coordinates

        Args:
            image_x, image_y: Pixel coordinates

        Returns:
            Optional[Tuple[float, float]]: Robot coordinates (x, y) or None if not calibrated
        """
        if not self.is_calibrated:
            logger.warning("Hand-eye calibration not available, using default")
            return self._default_image_to_robot(image_x, image_y)

        try:
            if hasattr(self, 'transform_matrix') and self.transform_matrix is not None:
                # Multi-point calibration
                img_point = np.array([image_x, image_y, 1])
                robot_x = np.dot(self.transform_matrix[0], img_point)
                robot_y = np.dot(self.transform_matrix[1], img_point)
            else:
                # 2-point calibration
                robot_x = self.x_scale * image_x + self.x_offset
                robot_y = self.y_scale * image_y + self.y_offset

            return float(robot_x), float(robot_y)

        except Exception as e:
            logger.error(f"Error converting coordinates: {e}")
            return None

    def robot_to_image(self, robot_x: float, robot_y: float) -> Optional[Tuple[int, int]]:
        """
        Convert robot coordinates to image coordinates (inverse transformation)

        Args:
            robot_x, robot_y: Robot coordinates

        Returns:
            Optional[Tuple[int, int]]: Image coordinates (x, y) or None if not calibrated
        """
        if not self.is_calibrated:
            logger.warning("Hand-eye calibration not available")
            return None

        try:
            if hasattr(self, 'transform_matrix') and self.transform_matrix is not None:
                # For multi-point, we'd need to solve the inverse (complex for general case)
                # For now, use approximate inverse with 2-point method
                logger.warning("Inverse transformation for multi-point calibration not implemented")
                return None
            else:
                # 2-point calibration inverse
                image_x = (robot_x - self.x_offset) / self.x_scale
                image_y = (robot_y - self.y_offset) / self.y_scale

            return int(round(image_x)), int(round(image_y))

        except Exception as e:
            logger.error(f"Error converting robot to image coordinates: {e}")
            return None

    def _default_image_to_robot(self, image_x: int, image_y: int) -> Tuple[float, float]:
        """
        Default image to robot conversion using built-in calibration points

        Args:
            image_x, image_y: Pixel coordinates

        Returns:
            Tuple[float, float]: Robot coordinates
        """
        # Use numpy interpolation with default points
        img_x_coords = [self.default_image_points[0][0], self.default_image_points[1][0]]
        img_y_coords = [self.default_image_points[1][1], self.default_image_points[0][1]]

        rob_x_coords = [self.default_robot_points[0][0], self.default_robot_points[1][0]]
        rob_y_coords = [self.default_robot_points[1][1], self.default_robot_points[0][1]]

        robot_x = np.interp(image_x, img_x_coords, rob_x_coords)
        robot_y = np.interp(image_y, img_y_coords, rob_y_coords)

        return float(robot_x), float(robot_y)

    def save_calibration(self) -> bool:
        """
        Save calibration data to file

        Returns:
            bool: True if save successful
        """
        try:
            os.makedirs(os.path.dirname(self.calibration_file), exist_ok=True)

            calibration_data = {
                'image_points': self.image_points,
                'robot_points': self.robot_points,
                'is_calibrated': self.is_calibrated,
            }

            # Add calibration parameters
            if hasattr(self, 'x_scale'):
                calibration_data.update({
                    'x_scale': self.x_scale,
                    'x_offset': self.x_offset,
                    'y_scale': self.y_scale,
                    'y_offset': self.y_offset,
                })

            if hasattr(self, 'transform_matrix') and self.transform_matrix is not None:
                calibration_data['transform_matrix'] = self.transform_matrix.tolist()

            with open(self.calibration_file, 'w') as f:
                json.dump(calibration_data, f, indent=2)

            logger.info(f"Calibration saved to {self.calibration_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving calibration: {e}")
            return False

    def load_calibration(self) -> bool:
        """
        Load calibration data from file

        Returns:
            bool: True if load successful
        """
        try:
            if not os.path.exists(self.calibration_file):
                logger.info("No calibration file found, using default calibration")
                return False

            with open(self.calibration_file, 'r') as f:
                calibration_data = json.load(f)

            self.image_points = calibration_data.get('image_points', [])
            self.robot_points = calibration_data.get('robot_points', [])
            self.is_calibrated = calibration_data.get('is_calibrated', False)

            # Load calibration parameters
            if 'x_scale' in calibration_data:
                self.x_scale = calibration_data['x_scale']
                self.x_offset = calibration_data['x_offset']
                self.y_scale = calibration_data['y_scale']
                self.y_offset = calibration_data['y_offset']

            if 'transform_matrix' in calibration_data:
                self.transform_matrix = np.array(calibration_data['transform_matrix'])

            logger.info(f"Calibration loaded from {self.calibration_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading calibration: {e}")
            return False

    def validate_calibration(self) -> bool:
        """
        Validate current calibration by checking accuracy

        Returns:
            bool: True if calibration appears accurate
        """
        if not self.is_calibrated or not self.image_points or not self.robot_points:
            return False

        try:
            # Test accuracy by converting back and forth
            total_error = 0.0
            for img_pt, rob_pt in zip(self.image_points, self.robot_points):
                converted_rob = self.image_to_robot(img_pt[0], img_pt[1])
                if converted_rob:
                    error = np.sqrt((converted_rob[0] - rob_pt[0])**2 +
                                  (converted_rob[1] - rob_pt[1])**2)
                    total_error += error

            avg_error = total_error / len(self.image_points)
            logger.info(f"Calibration validation: average error = {avg_error:.2f}mm")

            # Consider calibration valid if average error < 5mm
            return avg_error < 5.0

        except Exception as e:
            logger.error(f"Error validating calibration: {e}")
            return False