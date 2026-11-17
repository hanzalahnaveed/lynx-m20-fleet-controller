"""Single-process, read-only fleet monitor for two logical M20 robot slots."""

import json

import rclpy
from rclpy.node import Node
from drdds.msg import RobotStatus
from geometry_msgs.msg import PoseStamped

from .fleet_manager import FleetManager
from .ros2_localization_adapter import LocalizationAdapter


class FleetMonitor(Node):
    """Consumes robot status and poses, then reports readiness at 10 Hz.

    This node deliberately creates no velocity or hardware-command publisher.
    """

    def __init__(self):
        super().__init__("m20_fleet_monitor")

        self.declare_parameter("robot_name_map", "{}")
        self.declare_parameter("robot_a_pose_topic", "/robot_a/pose")
        self.declare_parameter("robot_b_pose_topic", "/robot_b/pose")

        raw_map = self.get_parameter("robot_name_map").value
        self.robot_name_map = json.loads(raw_map)
        if not isinstance(self.robot_name_map, dict):
            raise ValueError("robot_name_map must be a JSON object")

        unknown_slots = set(self.robot_name_map.values()) - {"robot_a", "robot_b"}
        if unknown_slots:
            raise ValueError(
                "robot_name_map values must be robot_a or robot_b; "
                f"got {sorted(unknown_slots)}"
            )

        self.fleet = FleetManager()

        # Share this exact FleetManager with the localization subscriptions.
        self.localization_node = LocalizationAdapter(self.fleet)

        self.status_subscription = self.create_subscription(
            RobotStatus,
            "/rl_deploy/status",
            self.status_callback,
            10,
        )
        self.report_publisher = self.create_publisher(
            # A human-readable diagnostic report, not a robot command.
            __import__("std_msgs.msg", fromlist=["String"]).String,
            "~/fleet_status",
            10,
        )
        self.timer = self.create_timer(0.1, self.publish_report)

        self.get_logger().warning(
            "READ-ONLY monitor started. No velocity or hardware command "
            "publisher is created. Robot identity mapping must be verified "
            "before interpreting two-robot status."
        )

    def status_callback(self, msg):
        robot_id = self.robot_name_map.get(msg.robot)
        if robot_id is None:
            self.get_logger().warning(
                f"Ignoring status with unmapped robot identity: {msg.robot!r}"
            )
            return

        self.fleet.update_status(robot_id, msg)

    def publish_report(self):
        from std_msgs.msg import String

        report = {}
        for robot_id in ("robot_a", "robot_b"):
            snapshot = self.fleet.snapshot(robot_id)
            pose = snapshot["pose"]
            target = snapshot["target"]

            report[robot_id] = {
                "connected": snapshot["connected"],
                "status_fresh": snapshot["status_fresh"],
                "telemetry_fresh": snapshot["telemetry_fresh"],
                "localization_fresh": pose is not None,
                "motion_enabled_in_software": snapshot["motion_enabled"],
                "current_state": snapshot["current_state"],
                "safety_mode": snapshot["safety_mode"],
                "command_timed_out": snapshot["command_timed_out"],
                "rejected_commands": snapshot["rejected_commands"],
                "pose": (
                    {"x": pose.x, "y": pose.y, "yaw": pose.yaw}
                    if pose is not None else None
                ),
                "target": (
                    {"x": target.x, "y": target.y}
                    if target is not None else None
                ),
            }

        message = String()
        message.data = json.dumps(report, sort_keys=True)
        self.report_publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = FleetMonitor()
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    executor.add_node(node.localization_node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.remove_node(node.localization_node)
        node.localization_node.destroy_node()
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
