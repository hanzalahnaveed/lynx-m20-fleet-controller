"""Read-only ROS 2 monitor combining SDK status and localization."""

import json

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from drdds.msg import RobotStatus
from std_msgs.msg import String

from .fleet_manager import FleetManager
from .fleet_report import build_fleet_report
from .ros2_localization_adapter import LocalizationAdapter


class FleetMonitor(Node):
    """Collect status and poses in one shared FleetManager instance.

    Publishes only a diagnostic std_msgs/String report. It has no velocity
    publisher and never sends commands to the robot SDK.
    """

    def __init__(self):
        super().__init__("m20_fleet_monitor")

        self.declare_parameter("robot_name_map", "{}")
        self.declare_parameter("robot_a_pose_topic", "/robot_a/pose")
        self.declare_parameter("robot_b_pose_topic", "/robot_b/pose")

        raw_map = self.get_parameter("robot_name_map").value
        try:
            self.robot_name_map = json.loads(raw_map)
        except json.JSONDecodeError as exc:
            raise ValueError("robot_name_map must contain valid JSON") from exc

        if not isinstance(self.robot_name_map, dict):
            raise ValueError("robot_name_map must be a JSON object")
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in self.robot_name_map.items()):
            raise ValueError("robot_name_map keys and values must be strings")

        invalid_slots = set(self.robot_name_map.values()) - {"robot_a", "robot_b"}
        if invalid_slots:
            raise ValueError(
                "robot_name_map values must be robot_a or robot_b; "
                f"invalid values: {sorted(invalid_slots)}"
            )
        if len(set(self.robot_name_map.values())) != len(self.robot_name_map):
            raise ValueError("robot_name_map cannot map multiple names to one slot")

        self.fleet = FleetManager()
        topic_a = self.get_parameter("robot_a_pose_topic").value
        topic_b = self.get_parameter("robot_b_pose_topic").value
        self.localization_node = LocalizationAdapter(
            self.fleet, topic_a=topic_a, topic_b=topic_b
        )

        self.status_subscription = self.create_subscription(
            RobotStatus, "/rl_deploy/status", self.status_callback, 10
        )
        self.report_publisher = self.create_publisher(String, "~/fleet_status", 10)
        self.timer = self.create_timer(0.1, self.publish_report)

        self.get_logger().warning(
            "READ-ONLY monitor active: publishes diagnostics only; "
            "no robot velocity or hardware-command publisher exists."
        )
        if not self.robot_name_map:
            self.get_logger().warning(
                "robot_name_map is empty; all SDK status messages will be ignored."
            )

    def status_callback(self, msg):
        robot_id = self.robot_name_map.get(msg.robot)
        if robot_id is None:
            self.get_logger().warning(
                f"Ignoring unmapped SDK robot identity: {msg.robot!r}"
            )
            return
        self.fleet.update_status(robot_id, msg)

    def publish_report(self):
        message = String()
        message.data = json.dumps(build_fleet_report(self.fleet), sort_keys=True)
        self.report_publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    monitor = FleetMonitor()
    executor = SingleThreadedExecutor()
    executor.add_node(monitor)
    executor.add_node(monitor.localization_node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.remove_node(monitor.localization_node)
        monitor.localization_node.destroy_node()
        executor.remove_node(monitor)
        monitor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
