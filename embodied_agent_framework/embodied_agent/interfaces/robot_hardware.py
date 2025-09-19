"""
Robot Hardware Interface - Abstract base class for robotic arm hardware
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np
from pydantic import BaseModel, Field


class RobotState(Enum):
    """Robot operation states"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    MOVING = "moving"
    IDLE = "idle"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"


class JointPosition(BaseModel):
    """Joint position data structure"""
    joint_id: int = Field(..., ge=1, le=6, description="Joint ID (1-6)")
    angle: float = Field(..., ge=-180, le=180, description="Joint angle in degrees")
    speed: Optional[float] = Field(None, ge=0, le=100, description="Movement speed (0-100)")


class CartesianPosition(BaseModel):
    """Cartesian position data structure"""
    x: float = Field(..., description="X coordinate in mm")
    y: float = Field(..., description="Y coordinate in mm")
    z: float = Field(..., description="Z coordinate in mm")
    rx: float = Field(0, description="Rotation around X axis in degrees")
    ry: float = Field(0, description="Rotation around Y axis in degrees")
    rz: float = Field(0, description="Rotation around Z axis in degrees")
    speed: Optional[float] = Field(None, ge=0, le=100, description="Movement speed (0-100)")


class RobotCapabilities(BaseModel):
    """Robot hardware capabilities"""
    degrees_of_freedom: int
    max_payload: float  # kg
    reach: float  # mm
    joint_limits: List[Tuple[float, float]]  # (min, max) angles for each joint
    coordinate_limits: Dict[str, Tuple[float, float]]  # x, y, z limits
    has_gripper: bool = False
    has_suction: bool = False
    has_force_sensor: bool = False


class RobotHardwareInterface(ABC):
    """
    Abstract base class for robot hardware interfaces.

    This interface provides a standardized way to interact with different
    robotic arm hardware while abstracting away vendor-specific details.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize robot hardware interface

        Args:
            config: Hardware-specific configuration parameters
        """
        self.config = config
        self.state = RobotState.DISCONNECTED
        self._capabilities: Optional[RobotCapabilities] = None

    @property
    def capabilities(self) -> RobotCapabilities:
        """Get robot capabilities"""
        if self._capabilities is None:
            self._capabilities = self.get_capabilities()
        return self._capabilities

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the robot hardware

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the robot hardware

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> RobotCapabilities:
        """
        Get robot hardware capabilities

        Returns:
            RobotCapabilities: Hardware capabilities
        """
        pass

    @abstractmethod
    async def get_joint_positions(self) -> List[JointPosition]:
        """
        Get current joint positions

        Returns:
            List[JointPosition]: Current joint positions
        """
        pass

    @abstractmethod
    async def get_cartesian_position(self) -> CartesianPosition:
        """
        Get current cartesian position

        Returns:
            CartesianPosition: Current end-effector position
        """
        pass

    @abstractmethod
    async def move_joints(self, positions: List[JointPosition], wait: bool = True) -> bool:
        """
        Move robot to specified joint positions

        Args:
            positions: Target joint positions
            wait: Whether to wait for movement completion

        Returns:
            bool: True if movement command successful
        """
        pass

    @abstractmethod
    async def move_cartesian(self, position: CartesianPosition, wait: bool = True) -> bool:
        """
        Move robot to specified cartesian position

        Args:
            position: Target cartesian position
            wait: Whether to wait for movement completion

        Returns:
            bool: True if movement command successful
        """
        pass

    @abstractmethod
    async def move_relative(self, delta: CartesianPosition, wait: bool = True) -> bool:
        """
        Move robot relative to current position

        Args:
            delta: Relative movement delta
            wait: Whether to wait for movement completion

        Returns:
            bool: True if movement command successful
        """
        pass

    @abstractmethod
    async def home(self) -> bool:
        """
        Move robot to home position

        Returns:
            bool: True if homing successful
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop robot movement immediately

        Returns:
            bool: True if stop successful
        """
        pass

    @abstractmethod
    async def emergency_stop(self) -> bool:
        """
        Emergency stop - disable all robot functions

        Returns:
            bool: True if emergency stop successful
        """
        pass

    @abstractmethod
    async def release_servos(self) -> bool:
        """
        Release servo motors (allows manual manipulation)

        Returns:
            bool: True if release successful
        """
        pass

    @abstractmethod
    async def is_moving(self) -> bool:
        """
        Check if robot is currently moving

        Returns:
            bool: True if robot is moving
        """
        pass

    @abstractmethod
    async def get_state(self) -> RobotState:
        """
        Get current robot state

        Returns:
            RobotState: Current robot state
        """
        pass

    # Optional gripper/end-effector methods
    async def gripper_open(self) -> bool:
        """
        Open gripper (if available)

        Returns:
            bool: True if successful, False if not supported
        """
        return False

    async def gripper_close(self) -> bool:
        """
        Close gripper (if available)

        Returns:
            bool: True if successful, False if not supported
        """
        return False

    async def suction_on(self) -> bool:
        """
        Turn on suction (if available)

        Returns:
            bool: True if successful, False if not supported
        """
        return False

    async def suction_off(self) -> bool:
        """
        Turn off suction (if available)

        Returns:
            bool: True if successful, False if not supported
        """
        return False