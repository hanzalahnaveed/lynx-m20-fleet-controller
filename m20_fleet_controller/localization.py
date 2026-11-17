import math
import time

from .controller_core import RobotPose


class LocalizationStore:
    """
    Stores the latest world-frame pose for each robot.

    Coordinates are in metres and yaw is in radians.
    This module does not estimate position itself.
    """

    def __init__(self, max_age=0.25):
        self.max_age = max_age
        self.poses = {}

    def update(self, robot_id, x, y, yaw, timestamp=None):
        if timestamp is None:
            timestamp = time.monotonic()

        values = (x, y, yaw, timestamp)

        if not all(math.isfinite(v) for v in values):
            raise ValueError("Pose contains a non-finite value")

        self.poses[robot_id] = RobotPose(
            x=float(x),
            y=float(y),
            yaw=float(yaw),
            timestamp=float(timestamp),
        )

    def get_pose(self, robot_id, now=None):
        if now is None:
            now = time.monotonic()

        pose = self.poses.get(robot_id)

        if pose is None:
            return None

        age = now - pose.timestamp

        if age < 0 or age > self.max_age:
            return None

        return pose

    def remove(self, robot_id):
        self.poses.pop(robot_id, None)
