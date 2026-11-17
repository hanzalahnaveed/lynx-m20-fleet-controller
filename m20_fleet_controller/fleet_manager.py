import time
from dataclasses import dataclass
from typing import Optional

from .controller_core import PositionController, Target, VelocityCommand
from .localization import LocalizationStore
from .safety_gate import SafetyGate


@dataclass
class RobotSlot:
    name: str
    target: Optional[Target] = None
    connected: bool = False
    status_received: bool = False
    telemetry_fresh: bool = False
    command_timed_out: bool = True
    current_state: str = "unknown"
    safety_mode: int = 0
    rejected_commands: int = 0
    last_status_time: float = 0.0
    last_command: VelocityCommand = None

    def __post_init__(self):
        if self.last_command is None:
            self.last_command = VelocityCommand()


class FleetManager:
    def __init__(self):
        self.controller = PositionController()
        self.localization = LocalizationStore(max_age=0.25)
        self.safety = SafetyGate()
        self.status_timeout = 0.5

        self.robots = {
            "robot_a": RobotSlot("robot_a"),
            "robot_b": RobotSlot("robot_b"),
        }

    def update_pose(self, robot_id, x, y, yaw, timestamp=None):
        self._get_robot(robot_id)
        self.localization.update(robot_id, x, y, yaw, timestamp)

    def update_status(self, robot_id, status, now=None):
        robot = self._get_robot(robot_id)

        if now is None:
            now = time.monotonic()

        robot.status_received = True
        robot.connected = True
        self.safety.set_connected(robot_id, True)
        robot.telemetry_fresh = bool(status.telemetry_fresh)
        robot.command_timed_out = bool(status.command_timed_out)
        robot.current_state = str(status.current_state)
        robot.safety_mode = int(status.safety_mode)
        robot.rejected_commands = int(status.rejected_commands)
        robot.last_status_time = now

        if not robot.telemetry_fresh:
            self.disable_motion(robot_id)

    def status_is_fresh(self, robot_id, now=None):
        robot = self._get_robot(robot_id)

        if now is None:
            now = time.monotonic()

        age = now - robot.last_status_time

        return (
            robot.status_received
            and 0 <= age <= self.status_timeout
            and robot.telemetry_fresh
        )

    def set_target(self, robot_id, target):
        self._get_robot(robot_id).target = target

    def set_connected(self, robot_id, connected):
        robot = self._get_robot(robot_id)
        robot.connected = bool(connected)

        self.safety.set_connected(robot_id, connected)

        if not connected:
            robot.status_received = False
            robot.telemetry_fresh = False
            self.safety.disable_motion(robot_id)
            robot.last_command = VelocityCommand()

    def enable_motion(self, robot_id, now=None):
        robot = self._get_robot(robot_id)

        if now is None:
            now = time.monotonic()

        pose = self.localization.get_pose(robot_id, now)

        if not robot.connected:
            raise RuntimeError("Cannot enable: robot is not connected")

        if not self.status_is_fresh(robot_id, now):
            raise RuntimeError("Cannot enable: robot status is missing or stale")

        if pose is None:
            raise RuntimeError("Cannot enable: localization is missing or stale")

        if robot.safety_mode != 0:
            raise RuntimeError("Cannot enable: robot safety mode is active")

        self.safety.enable_motion(robot_id)

    def disable_motion(self, robot_id):
        robot = self._get_robot(robot_id)
        self.safety.disable_motion(robot_id)
        robot.last_command = VelocityCommand()

    def stop(self, robot_id):
        robot = self._get_robot(robot_id)
        self.safety.disable_motion(robot_id)
        robot.last_command = VelocityCommand()
        robot.target = None

    def preview_calculate(self, robot_id, now=None):
        """Calculate a dry-run candidate without enabling or storing motion."""
        robot = self._get_robot(robot_id)

        if now is None:
            now = time.monotonic()

        pose = self.localization.get_pose(robot_id, now)
        if (
            not self.status_is_fresh(robot_id, now)
            or pose is None
            or robot.target is None
            or robot.safety_mode != 0
        ):
            return VelocityCommand()

        # This is a local calculation only. It does not change the safety
        # gate, last_command, or publish any ROS or hardware message.
        return self.controller.calculate(pose, robot.target, now)

    def calculate(self, robot_id, now=None):
        robot = self._get_robot(robot_id)

        if now is None:
            now = time.monotonic()

        pose = self.localization.get_pose(robot_id, now)

        if not self.status_is_fresh(robot_id, now):
            self.safety.disable_motion(robot_id)
            robot.last_command = VelocityCommand()
            return robot.last_command

        if (
            not self.safety.allow_command(robot_id, pose is not None)
            or robot.target is None
            or robot.safety_mode != 0
        ):
            robot.last_command = VelocityCommand()
            return robot.last_command

        robot.last_command = self.controller.calculate(
            pose, robot.target, now
        )
        return robot.last_command

    def snapshot(self, robot_id, now=None):
        robot = self._get_robot(robot_id)

        if now is None:
            now = time.monotonic()

        return {
            "name": robot.name,
            "connected": robot.connected,
            "status_fresh": self.status_is_fresh(robot_id, now),
            "telemetry_fresh": robot.telemetry_fresh,
            "command_timed_out": robot.command_timed_out,
            "current_state": robot.current_state,
            "safety_mode": robot.safety_mode,
            "rejected_commands": robot.rejected_commands,
            "pose": self.localization.get_pose(robot_id, now),
            "target": robot.target,
            "motion_enabled": self.safety.states[robot_id].motion_enabled,
            "velocity": robot.last_command,
        }

    def _get_robot(self, robot_id):
        if robot_id not in self.robots:
            raise ValueError(f"Unknown robot ID: {robot_id}")
        return self.robots[robot_id]
