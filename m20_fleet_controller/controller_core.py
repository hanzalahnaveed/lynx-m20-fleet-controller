import math
from dataclasses import dataclass


@dataclass
class RobotPose:
    x: float
    y: float
    yaw: float
    timestamp: float


@dataclass
class VelocityCommand:
    forward: float = 0.0
    sideways: float = 0.0
    yaw_rate: float = 0.0


@dataclass
class Target:
    x: float
    y: float


class PositionController:
    """
    Converts a shared-frame X/Y target into body-frame velocity.

    This module only calculates commands. It does not communicate
    with a robot or publish ROS messages.
    """

    def __init__(
        self,
        max_forward=0.20,
        max_sideways=0.15,
        max_yaw_rate=0.30,
        position_tolerance=0.10,
        pose_timeout=0.25,
        position_gain=0.5,
        heading_gain=1.0,
    ):
        self.max_forward = max_forward
        self.max_sideways = max_sideways
        self.max_yaw_rate = max_yaw_rate
        self.position_tolerance = position_tolerance
        self.pose_timeout = pose_timeout
        self.position_gain = position_gain
        self.heading_gain = heading_gain

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def clamp(value, limit):
        return max(-limit, min(limit, value))

    def calculate(self, pose, target, now):
        # Never calculate movement from stale localization.
        if now - pose.timestamp > self.pose_timeout:
            return VelocityCommand()

        if not all(math.isfinite(v) for v in (
            pose.x, pose.y, pose.yaw, target.x, target.y, now
        )):
            return VelocityCommand()

        dx = target.x - pose.x
        dy = target.y - pose.y
        distance = math.hypot(dx, dy)

        if distance <= self.position_tolerance:
            return VelocityCommand()

        # Convert the target direction from world coordinates
        # into the robot's body coordinate frame.
        cos_yaw = math.cos(pose.yaw)
        sin_yaw = math.sin(pose.yaw)

        body_x = cos_yaw * dx + sin_yaw * dy
        body_y = -sin_yaw * dx + cos_yaw * dy

        forward = self.clamp(
            self.position_gain * body_x,
            self.max_forward
        )
        sideways = self.clamp(
            self.position_gain * body_y,
            self.max_sideways
        )

        # Rotate toward the direction of travel.
        desired_yaw = math.atan2(dy, dx)
        yaw_error = self.normalize_angle(desired_yaw - pose.yaw)

        yaw_rate = self.clamp(
            self.heading_gain * yaw_error,
            self.max_yaw_rate
        )

        return VelocityCommand(
            forward=forward,
            sideways=sideways,
            yaw_rate=yaw_rate,
        )
