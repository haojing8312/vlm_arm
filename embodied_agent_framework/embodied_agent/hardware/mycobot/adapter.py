"""
MyCobot Hardware Adapter Implementation
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from pymycobot.mycobot import MyCobot
    from pymycobot import PI_PORT, PI_BAUD
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    logger.warning("MyCobot hardware libraries not available - running in simulation mode")
    HARDWARE_AVAILABLE = False

from ..interfaces.robot_hardware import (
    RobotHardwareInterface,
    RobotState,
    JointPosition,
    CartesianPosition,
    RobotCapabilities,
)


class MyCobotAdapter(RobotHardwareInterface):
    """
    Hardware adapter for Elephant Robotics MyCobot 280 robotic arm
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MyCobot adapter

        Args:
            config: Configuration dictionary with MyCobot-specific parameters
        """
        super().__init__(config)

        # Hardware configuration
        self.port = config.get('port', PI_PORT)
        self.baudrate = config.get('baudrate', PI_BAUD)
        self.simulation_mode = config.get('simulation_mode', not HARDWARE_AVAILABLE)

        # GPIO configuration for suction pump
        self.suction_pin_1 = config.get('suction_pin_1', 20)
        self.suction_pin_2 = config.get('suction_pin_2', 21)

        # Hardware instances
        self._robot: Optional[MyCobot] = None
        self._gpio_initialized = False

        # Movement parameters
        self.default_speed = config.get('default_speed', 40)
        self.safe_height = config.get('safe_height', 230)

        # Current state tracking
        self._current_joints: List[float] = [0.0] * 6
        self._current_coords: List[float] = [0.0] * 6
        self._is_moving = False

    async def connect(self) -> bool:
        """Connect to MyCobot hardware"""
        try:
            if self.simulation_mode:
                logger.info("MyCobot: Running in simulation mode")
                self.state = RobotState.CONNECTED
                return True

            # Initialize robot connection
            self._robot = MyCobot(self.port, self.baudrate)
            self._robot.set_fresh_mode(0)  # Set interpolation mode

            # Initialize GPIO for suction pump
            self._init_gpio()

            # Test connection
            await asyncio.sleep(0.1)
            self.state = RobotState.CONNECTED
            logger.info(f"MyCobot connected on {self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MyCobot: {e}")
            self.state = RobotState.ERROR
            return False

    async def disconnect(self) -> bool:
        """Disconnect from MyCobot hardware"""
        try:
            if self._robot and not self.simulation_mode:
                self._robot.release_all_servos()

            if self._gpio_initialized:
                GPIO.cleanup()
                self._gpio_initialized = False

            self.state = RobotState.DISCONNECTED
            logger.info("MyCobot disconnected")
            return True

        except Exception as e:
            logger.error(f"Error during MyCobot disconnection: {e}")
            return False

    def get_capabilities(self) -> RobotCapabilities:
        """Get MyCobot 280 capabilities"""
        return RobotCapabilities(
            degrees_of_freedom=6,
            max_payload=0.25,  # 250g
            reach=280,  # 280mm
            joint_limits=[
                (-165, 165),  # Joint 1
                (-165, 165),  # Joint 2
                (-165, 165),  # Joint 3
                (-165, 165),  # Joint 4
                (-165, 165),  # Joint 5
                (-175, 175),  # Joint 6
            ],
            coordinate_limits={
                'x': (-280, 280),
                'y': (-280, 280),
                'z': (-280, 400),
            },
            has_gripper=False,
            has_suction=True,
            has_force_sensor=False,
        )

    async def get_joint_positions(self) -> List[JointPosition]:
        """Get current joint positions"""
        try:
            if self.simulation_mode:
                angles = self._current_joints
            else:
                angles = self._robot.get_angles()
                if angles:
                    self._current_joints = angles
                else:
                    angles = self._current_joints

            return [
                JointPosition(joint_id=i+1, angle=angle)
                for i, angle in enumerate(angles)
            ]

        except Exception as e:
            logger.error(f"Error getting joint positions: {e}")
            return [JointPosition(joint_id=i+1, angle=0.0) for i in range(6)]

    async def get_cartesian_position(self) -> CartesianPosition:
        """Get current cartesian position"""
        try:
            if self.simulation_mode:
                coords = self._current_coords
            else:
                coords = self._robot.get_coords()
                if coords:
                    self._current_coords = coords
                else:
                    coords = self._current_coords

            return CartesianPosition(
                x=coords[0], y=coords[1], z=coords[2],
                rx=coords[3], ry=coords[4], rz=coords[5]
            )

        except Exception as e:
            logger.error(f"Error getting cartesian position: {e}")
            return CartesianPosition(x=0, y=0, z=0, rx=0, ry=0, rz=0)

    async def move_joints(self, positions: List[JointPosition], wait: bool = True) -> bool:
        """Move to specified joint positions"""
        try:
            angles = [pos.angle for pos in positions]
            speed = positions[0].speed or self.default_speed

            if self.simulation_mode:
                logger.info(f"Simulation: Moving joints to {angles}")
                self._current_joints = angles[:]
                if wait:
                    await asyncio.sleep(2.0)  # Simulate movement time
            else:
                self._robot.send_angles(angles, speed)
                if wait:
                    await self._wait_for_movement_completion()

            return True

        except Exception as e:
            logger.error(f"Error moving joints: {e}")
            return False

    async def move_cartesian(self, position: CartesianPosition, wait: bool = True) -> bool:
        """Move to specified cartesian position"""
        try:
            coords = [position.x, position.y, position.z,
                     position.rx, position.ry, position.rz]
            speed = position.speed or self.default_speed

            if self.simulation_mode:
                logger.info(f"Simulation: Moving to cartesian {coords}")
                self._current_coords = coords[:]
                if wait:
                    await asyncio.sleep(3.0)  # Simulate movement time
            else:
                self._robot.send_coords(coords, speed, 0)
                if wait:
                    await self._wait_for_movement_completion()

            return True

        except Exception as e:
            logger.error(f"Error moving to cartesian position: {e}")
            return False

    async def move_relative(self, delta: CartesianPosition, wait: bool = True) -> bool:
        """Move relative to current position"""
        try:
            current = await self.get_cartesian_position()
            target = CartesianPosition(
                x=current.x + delta.x,
                y=current.y + delta.y,
                z=current.z + delta.z,
                rx=current.rx + delta.rx,
                ry=current.ry + delta.ry,
                rz=current.rz + delta.rz,
                speed=delta.speed
            )
            return await self.move_cartesian(target, wait)

        except Exception as e:
            logger.error(f"Error moving relative: {e}")
            return False

    async def home(self) -> bool:
        """Move to home position (all joints at 0 degrees)"""
        try:
            home_positions = [JointPosition(joint_id=i+1, angle=0.0) for i in range(6)]
            return await self.move_joints(home_positions, wait=True)

        except Exception as e:
            logger.error(f"Error homing robot: {e}")
            return False

    async def stop(self) -> bool:
        """Stop robot movement"""
        try:
            if not self.simulation_mode and self._robot:
                self._robot.stop()
            self._is_moving = False
            logger.info("Robot movement stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping robot: {e}")
            return False

    async def emergency_stop(self) -> bool:
        """Emergency stop"""
        try:
            await self.stop()
            await self.release_servos()
            self.state = RobotState.EMERGENCY_STOP
            logger.warning("Emergency stop activated")
            return True

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return False

    async def release_servos(self) -> bool:
        """Release servo motors"""
        try:
            if not self.simulation_mode and self._robot:
                self._robot.release_all_servos()
            logger.info("Servo motors released")
            return True

        except Exception as e:
            logger.error(f"Error releasing servos: {e}")
            return False

    async def is_moving(self) -> bool:
        """Check if robot is moving"""
        if self.simulation_mode:
            return self._is_moving

        try:
            if self._robot:
                return self._robot.is_moving()
            return False

        except Exception as e:
            logger.error(f"Error checking movement status: {e}")
            return False

    async def get_state(self) -> RobotState:
        """Get current robot state"""
        if await self.is_moving():
            return RobotState.MOVING
        return self.state

    async def suction_on(self) -> bool:
        """Turn on suction pump"""
        try:
            if self.simulation_mode:
                logger.info("Simulation: Suction pump ON")
                return True

            if self._gpio_initialized:
                GPIO.output(self.suction_pin_1, 0)  # Turn on suction
                logger.info("Suction pump activated")
                return True
            else:
                logger.error("GPIO not initialized")
                return False

        except Exception as e:
            logger.error(f"Error turning on suction: {e}")
            return False

    async def suction_off(self) -> bool:
        """Turn off suction pump"""
        try:
            if self.simulation_mode:
                logger.info("Simulation: Suction pump OFF")
                return True

            if self._gpio_initialized:
                GPIO.output(self.suction_pin_1, 1)  # Turn off suction
                logger.info("Suction pump deactivated")
                return True
            else:
                logger.error("GPIO not initialized")
                return False

        except Exception as e:
            logger.error(f"Error turning off suction: {e}")
            return False

    def _init_gpio(self):
        """Initialize GPIO for suction pump control"""
        if self.simulation_mode:
            self._gpio_initialized = True
            return

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.suction_pin_1, GPIO.OUT)
            GPIO.setup(self.suction_pin_2, GPIO.OUT)
            GPIO.output(self.suction_pin_1, 1)  # Initially off
            self._gpio_initialized = True
            logger.info("GPIO initialized for suction pump")

        except Exception as e:
            logger.error(f"Error initializing GPIO: {e}")

    async def _wait_for_movement_completion(self, timeout: float = 30.0):
        """Wait for robot movement to complete"""
        start_time = time.time()

        while await self.is_moving():
            if time.time() - start_time > timeout:
                logger.warning("Movement timeout reached")
                break
            await asyncio.sleep(0.1)

        # Additional settling time
        await asyncio.sleep(0.5)