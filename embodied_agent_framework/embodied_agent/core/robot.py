"""
Robot Controller - High-level robot control abstraction
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
import numpy as np

from ..interfaces.robot_hardware import (
    RobotHardwareInterface,
    RobotState,
    JointPosition,
    CartesianPosition,
)
from ..utils.calibration import HandEyeCalibration
from ..utils.motion_planning import MotionPlanner


class RobotController:
    """
    High-level robot controller that provides standardized robot operations
    with safety checks, calibration, and motion planning capabilities.
    """

    def __init__(self, hardware: RobotHardwareInterface, config: Dict[str, Any]):
        """
        Initialize robot controller

        Args:
            hardware: Robot hardware interface
            config: Controller configuration
        """
        self.hardware = hardware
        self.config = config

        # Safety parameters
        self.max_speed = config.get('max_speed', 50)
        self.safe_height = config.get('safe_height', 200)
        self.workspace_limits = config.get('workspace_limits', {
            'x': (-250, 250),
            'y': (-250, 250),
            'z': (50, 350)
        })

        # Components
        self.calibration = HandEyeCalibration(config.get('calibration', {}))
        self.motion_planner = MotionPlanner(config.get('motion_planning', {}))

        # State tracking
        self._is_calibrated = False
        self._emergency_stop_active = False

    async def initialize(self) -> bool:
        """
        Initialize robot controller

        Returns:
            bool: True if initialization successful
        """
        try:
            # Connect to hardware
            if not await self.hardware.connect():
                logger.error("Failed to connect to robot hardware")
                return False

            # Load calibration if available
            if self.calibration.load_calibration():
                self._is_calibrated = True
                logger.info("Hand-eye calibration loaded")

            logger.info("Robot controller initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing robot controller: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        Shutdown robot controller safely

        Returns:
            bool: True if shutdown successful
        """
        try:
            # Stop any ongoing movement
            await self.hardware.stop()

            # Move to safe position
            await self.move_to_safe_position()

            # Disconnect hardware
            await self.hardware.disconnect()

            logger.info("Robot controller shutdown complete")
            return True

        except Exception as e:
            logger.error(f"Error during robot shutdown: {e}")
            return False

    async def emergency_stop(self) -> bool:
        """
        Emergency stop - immediately halt all robot operations

        Returns:
            bool: True if emergency stop successful
        """
        try:
            self._emergency_stop_active = True
            result = await self.hardware.emergency_stop()
            logger.warning("EMERGENCY STOP ACTIVATED")
            return result

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return False

    async def reset_emergency_stop(self) -> bool:
        """
        Reset emergency stop state

        Returns:
            bool: True if reset successful
        """
        try:
            if self._emergency_stop_active:
                self._emergency_stop_active = False
                await self.hardware.connect()  # Reconnect if needed
                logger.info("Emergency stop reset")
                return True
            return True

        except Exception as e:
            logger.error(f"Error resetting emergency stop: {e}")
            return False

    async def move_to_position(self, x: float, y: float, z: float,
                             speed: Optional[float] = None,
                             safe_approach: bool = True) -> bool:
        """
        Move robot to specified position with safety checks

        Args:
            x, y, z: Target coordinates
            speed: Movement speed (0-100)
            safe_approach: Whether to use safe approach trajectory

        Returns:
            bool: True if movement successful
        """
        if self._emergency_stop_active:
            logger.error("Cannot move - emergency stop active")
            return False

        try:
            # Validate position
            if not self._is_position_safe(x, y, z):
                logger.error(f"Position ({x}, {y}, {z}) outside safe workspace")
                return False

            target = CartesianPosition(x=x, y=y, z=z, speed=speed)

            if safe_approach:
                # Use safe approach trajectory
                return await self._safe_approach_move(target)
            else:
                # Direct movement
                return await self.hardware.move_cartesian(target, wait=True)

        except Exception as e:
            logger.error(f"Error moving to position: {e}")
            return False

    async def pick_and_place(self, pick_pos: Tuple[float, float, float],
                           place_pos: Tuple[float, float, float],
                           pick_height: float = 90,
                           place_height: float = 100) -> bool:
        """
        Perform pick and place operation

        Args:
            pick_pos: (x, y, z) coordinates to pick from
            place_pos: (x, y, z) coordinates to place at
            pick_height: Height for picking object
            place_height: Height for placing object

        Returns:
            bool: True if operation successful
        """
        try:
            logger.info(f"Starting pick and place: {pick_pos} -> {place_pos}")

            # 1. Move to pick position (safe height)
            if not await self.move_to_position(pick_pos[0], pick_pos[1], self.safe_height):
                return False

            # 2. Turn on suction
            if not await self.hardware.suction_on():
                logger.error("Failed to activate suction")
                return False

            # 3. Move down to pick height
            if not await self.move_to_position(pick_pos[0], pick_pos[1], pick_height):
                await self.hardware.suction_off()
                return False

            # Wait for suction to engage
            await asyncio.sleep(1.0)

            # 4. Lift object to safe height
            if not await self.move_to_position(pick_pos[0], pick_pos[1], self.safe_height):
                await self.hardware.suction_off()
                return False

            # 5. Move to place position (safe height)
            if not await self.move_to_position(place_pos[0], place_pos[1], self.safe_height):
                await self.hardware.suction_off()
                return False

            # 6. Move down to place height
            if not await self.move_to_position(place_pos[0], place_pos[1], place_height):
                await self.hardware.suction_off()
                return False

            # 7. Turn off suction
            if not await self.hardware.suction_off():
                logger.warning("Failed to deactivate suction")

            # 8. Return to safe height
            await self.move_to_position(place_pos[0], place_pos[1], self.safe_height)

            logger.info("Pick and place operation completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during pick and place: {e}")
            await self.hardware.suction_off()  # Ensure suction is off
            return False

    async def move_to_home(self) -> bool:
        """
        Move robot to home position

        Returns:
            bool: True if successful
        """
        try:
            return await self.hardware.home()

        except Exception as e:
            logger.error(f"Error moving to home: {e}")
            return False

    async def move_to_safe_position(self) -> bool:
        """
        Move robot to a predefined safe position

        Returns:
            bool: True if successful
        """
        try:
            # Move to home position as safe position
            return await self.move_to_home()

        except Exception as e:
            logger.error(f"Error moving to safe position: {e}")
            return False

    async def calibrate_hand_eye(self, image_coords: List[Tuple[int, int]],
                               robot_coords: List[Tuple[float, float]]) -> bool:
        """
        Perform hand-eye calibration

        Args:
            image_coords: List of pixel coordinates
            robot_coords: List of corresponding robot coordinates

        Returns:
            bool: True if calibration successful
        """
        try:
            if len(image_coords) < 2 or len(robot_coords) < 2:
                logger.error("Need at least 2 calibration points")
                return False

            success = self.calibration.calibrate(image_coords, robot_coords)
            if success:
                self._is_calibrated = True
                logger.info("Hand-eye calibration completed")
                return True
            else:
                logger.error("Hand-eye calibration failed")
                return False

        except Exception as e:
            logger.error(f"Error during calibration: {e}")
            return False

    def image_to_robot_coords(self, image_x: int, image_y: int) -> Optional[Tuple[float, float]]:
        """
        Convert image coordinates to robot coordinates

        Args:
            image_x, image_y: Pixel coordinates

        Returns:
            Optional[Tuple[float, float]]: Robot coordinates or None if not calibrated
        """
        if not self._is_calibrated:
            logger.error("Hand-eye calibration not available")
            return None

        return self.calibration.image_to_robot(image_x, image_y)

    async def get_current_position(self) -> Optional[CartesianPosition]:
        """
        Get current robot position

        Returns:
            Optional[CartesianPosition]: Current position or None if error
        """
        try:
            return await self.hardware.get_cartesian_position()

        except Exception as e:
            logger.error(f"Error getting current position: {e}")
            return None

    async def get_robot_state(self) -> RobotState:
        """
        Get current robot state

        Returns:
            RobotState: Current robot state
        """
        try:
            return await self.hardware.get_state()

        except Exception as e:
            logger.error(f"Error getting robot state: {e}")
            return RobotState.ERROR

    def _is_position_safe(self, x: float, y: float, z: float) -> bool:
        """
        Check if position is within safe workspace limits

        Args:
            x, y, z: Position coordinates

        Returns:
            bool: True if position is safe
        """
        x_min, x_max = self.workspace_limits['x']
        y_min, y_max = self.workspace_limits['y']
        z_min, z_max = self.workspace_limits['z']

        return (x_min <= x <= x_max and
                y_min <= y <= y_max and
                z_min <= z <= z_max)

    async def _safe_approach_move(self, target: CartesianPosition) -> bool:
        """
        Move to target using safe approach trajectory

        Args:
            target: Target position

        Returns:
            bool: True if movement successful
        """
        try:
            # First move to safe height above target
            safe_target = CartesianPosition(
                x=target.x, y=target.y, z=self.safe_height,
                rx=target.rx, ry=target.ry, rz=target.rz,
                speed=target.speed
            )

            if not await self.hardware.move_cartesian(safe_target, wait=True):
                return False

            # Then move down to target
            return await self.hardware.move_cartesian(target, wait=True)

        except Exception as e:
            logger.error(f"Error in safe approach move: {e}")
            return False