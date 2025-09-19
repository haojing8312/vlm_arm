"""
Motion Planning utilities for safe robot movement
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from loguru import logger

from ..interfaces.robot_hardware import CartesianPosition


class MotionPlanner:
    """
    Motion planner for generating safe robot trajectories
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize motion planner

        Args:
            config: Motion planning configuration
        """
        self.config = config

        # Planning parameters
        self.max_velocity = config.get('max_velocity', 100)  # mm/s
        self.max_acceleration = config.get('max_acceleration', 500)  # mm/s²
        self.path_resolution = config.get('path_resolution', 10)  # mm
        self.safe_height = config.get('safe_height', 200)  # mm

        # Workspace limits
        self.workspace_limits = config.get('workspace_limits', {
            'x': (-250, 250),
            'y': (-250, 250),
            'z': (50, 350)
        })

        # Obstacles (simplified as spheres for now)
        self.obstacles = config.get('obstacles', [])

    def plan_trajectory(self, start: CartesianPosition,
                       goal: CartesianPosition,
                       use_safe_height: bool = True) -> List[CartesianPosition]:
        """
        Plan trajectory from start to goal position

        Args:
            start: Starting position
            goal: Goal position
            use_safe_height: Whether to use safe height approach

        Returns:
            List[CartesianPosition]: Trajectory waypoints
        """
        try:
            if use_safe_height:
                return self._plan_safe_height_trajectory(start, goal)
            else:
                return self._plan_direct_trajectory(start, goal)

        except Exception as e:
            logger.error(f"Error planning trajectory: {e}")
            return [start, goal]  # Fallback to direct path

    def _plan_safe_height_trajectory(self, start: CartesianPosition,
                                   goal: CartesianPosition) -> List[CartesianPosition]:
        """
        Plan trajectory using safe height approach

        Args:
            start: Starting position
            goal: Goal position

        Returns:
            List[CartesianPosition]: Trajectory waypoints
        """
        waypoints = []

        # 1. Start position
        waypoints.append(start)

        # 2. Lift to safe height (if not already there)
        if start.z < self.safe_height:
            safe_start = CartesianPosition(
                x=start.x, y=start.y, z=self.safe_height,
                rx=start.rx, ry=start.ry, rz=start.rz
            )
            waypoints.append(safe_start)

        # 3. Move horizontally to goal position at safe height
        safe_goal = CartesianPosition(
            x=goal.x, y=goal.y, z=self.safe_height,
            rx=goal.rx, ry=goal.ry, rz=goal.rz
        )
        waypoints.append(safe_goal)

        # 4. Descend to goal position (if not at safe height)
        if goal.z < self.safe_height:
            waypoints.append(goal)

        return waypoints

    def _plan_direct_trajectory(self, start: CartesianPosition,
                              goal: CartesianPosition) -> List[CartesianPosition]:
        """
        Plan direct trajectory with collision checking

        Args:
            start: Starting position
            goal: Goal position

        Returns:
            List[CartesianPosition]: Trajectory waypoints
        """
        waypoints = []

        # Calculate distance
        distance = np.sqrt((goal.x - start.x)**2 + (goal.y - start.y)**2 + (goal.z - start.z)**2)

        # Number of intermediate waypoints
        num_waypoints = max(2, int(distance / self.path_resolution))

        # Generate intermediate waypoints
        for i in range(num_waypoints + 1):
            t = i / num_waypoints

            # Linear interpolation
            x = start.x + t * (goal.x - start.x)
            y = start.y + t * (goal.y - start.y)
            z = start.z + t * (goal.z - start.z)

            # Interpolate orientation
            rx = start.rx + t * (goal.rx - start.rx)
            ry = start.ry + t * (goal.ry - start.ry)
            rz = start.rz + t * (goal.rz - start.rz)

            waypoint = CartesianPosition(x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)

            # Check for collisions
            if self.is_position_valid(waypoint):
                waypoints.append(waypoint)
            else:
                logger.warning(f"Collision detected at waypoint {i}, using safe height approach")
                return self._plan_safe_height_trajectory(start, goal)

        return waypoints

    def is_position_valid(self, position: CartesianPosition) -> bool:
        """
        Check if position is valid (within workspace and collision-free)

        Args:
            position: Position to check

        Returns:
            bool: True if position is valid
        """
        # Check workspace limits
        if not self._is_within_workspace(position):
            return False

        # Check collisions with obstacles
        if not self._is_collision_free(position):
            return False

        return True

    def _is_within_workspace(self, position: CartesianPosition) -> bool:
        """
        Check if position is within workspace limits

        Args:
            position: Position to check

        Returns:
            bool: True if within workspace
        """
        x_min, x_max = self.workspace_limits['x']
        y_min, y_max = self.workspace_limits['y']
        z_min, z_max = self.workspace_limits['z']

        return (x_min <= position.x <= x_max and
                y_min <= position.y <= y_max and
                z_min <= position.z <= z_max)

    def _is_collision_free(self, position: CartesianPosition) -> bool:
        """
        Check if position is collision-free

        Args:
            position: Position to check

        Returns:
            bool: True if collision-free
        """
        for obstacle in self.obstacles:
            if self._check_sphere_collision(position, obstacle):
                return False

        return True

    def _check_sphere_collision(self, position: CartesianPosition,
                              obstacle: Dict[str, Any]) -> bool:
        """
        Check collision with spherical obstacle

        Args:
            position: Position to check
            obstacle: Obstacle definition with 'center' and 'radius'

        Returns:
            bool: True if collision detected
        """
        try:
            center = obstacle['center']  # [x, y, z]
            radius = obstacle['radius']

            distance = np.sqrt((position.x - center[0])**2 +
                             (position.y - center[1])**2 +
                             (position.z - center[2])**2)

            return distance <= radius

        except KeyError:
            logger.warning("Invalid obstacle definition")
            return False

    def smooth_trajectory(self, waypoints: List[CartesianPosition],
                         smoothing_factor: float = 0.1) -> List[CartesianPosition]:
        """
        Apply smoothing to trajectory waypoints

        Args:
            waypoints: Original waypoints
            smoothing_factor: Smoothing strength (0-1)

        Returns:
            List[CartesianPosition]: Smoothed waypoints
        """
        if len(waypoints) < 3:
            return waypoints

        try:
            smoothed = [waypoints[0]]  # Keep first waypoint

            for i in range(1, len(waypoints) - 1):
                prev_wp = waypoints[i - 1]
                curr_wp = waypoints[i]
                next_wp = waypoints[i + 1]

                # Apply smoothing
                smooth_x = curr_wp.x + smoothing_factor * (
                    (prev_wp.x + next_wp.x) / 2 - curr_wp.x
                )
                smooth_y = curr_wp.y + smoothing_factor * (
                    (prev_wp.y + next_wp.y) / 2 - curr_wp.y
                )
                smooth_z = curr_wp.z + smoothing_factor * (
                    (prev_wp.z + next_wp.z) / 2 - curr_wp.z
                )

                smoothed_wp = CartesianPosition(
                    x=smooth_x, y=smooth_y, z=smooth_z,
                    rx=curr_wp.rx, ry=curr_wp.ry, rz=curr_wp.rz
                )

                # Validate smoothed waypoint
                if self.is_position_valid(smoothed_wp):
                    smoothed.append(smoothed_wp)
                else:
                    smoothed.append(curr_wp)  # Keep original if invalid

            smoothed.append(waypoints[-1])  # Keep last waypoint
            return smoothed

        except Exception as e:
            logger.error(f"Error smoothing trajectory: {e}")
            return waypoints

    def calculate_trajectory_time(self, waypoints: List[CartesianPosition]) -> float:
        """
        Calculate estimated time to execute trajectory

        Args:
            waypoints: Trajectory waypoints

        Returns:
            float: Estimated execution time in seconds
        """
        if len(waypoints) < 2:
            return 0.0

        total_time = 0.0

        for i in range(1, len(waypoints)):
            prev_wp = waypoints[i - 1]
            curr_wp = waypoints[i]

            # Calculate distance
            distance = np.sqrt((curr_wp.x - prev_wp.x)**2 +
                             (curr_wp.y - prev_wp.y)**2 +
                             (curr_wp.z - prev_wp.z)**2)

            # Estimate time based on max velocity and acceleration
            # Simplified trapezoidal velocity profile
            accel_time = self.max_velocity / self.max_acceleration
            accel_distance = 0.5 * self.max_acceleration * accel_time**2

            if distance <= 2 * accel_distance:
                # Triangular profile (short distance)
                total_time += 2 * np.sqrt(distance / self.max_acceleration)
            else:
                # Trapezoidal profile
                cruise_distance = distance - 2 * accel_distance
                cruise_time = cruise_distance / self.max_velocity
                total_time += 2 * accel_time + cruise_time

        return total_time