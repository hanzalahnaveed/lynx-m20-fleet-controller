"""Read-only ROS 2 monitor with local position-controller previews."""

import json

from ament_index_python.packages import get_package_share_directory
from .dashboard_server import DashboardServer

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from drdds.msg import RobotStatus
from std_msgs.msg import String

from .controller_core import Target
from .fleet_manager import FleetManager
from .fleet_report import build_fleet_report
from .ros2_localization_adapter import LocalizationAdapter


class FleetMonitor(Node):
    """Collect status/poses and publish diagnostics plus dry-run previews.

    Preview values are calculated locally. This node has no velocity
    publisher and never sends commands to the robot SDK.
    """

    def __init__(self):
        super().__init__("m20_fleet_monitor")

        self.declare_parameter("robot_name_map", "{}")
        self.declare_parameter("robot_a_pose_topic", "/robot_a/pose")
        self.declare_parameter("robot_b_pose_topic", "/robot_b/pose")
        self.declare_parameter("robot_a_target_x", 2.0)
        self.declare_parameter("robot_a_target_y", 2.0)
        self.declare_parameter("robot_b_target_x", 4.0)
        self.declare_parameter("robot_b_target_y", 6.0)
        self.declare_parameter("dashboard_host", "127.0.0.1")
        self.declare_parameter("dashboard_port", 8765)

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
        self.fleet.set_target(
            "robot_a",
            Target(
                float(self.get_parameter("robot_a_target_x").value),
                float(self.get_parameter("robot_a_target_y").value),
            ),
        )
        self.fleet.set_target(
            "robot_b",
            Target(
                float(self.get_parameter("robot_b_target_x").value),
                float(self.get_parameter("robot_b_target_y").value),
            ),
        )

        topic_a = self.get_parameter("robot_a_pose_topic").value
        topic_b = self.get_parameter("robot_b_pose_topic").value
        self.localization_node = LocalizationAdapter(
            self.fleet,
            topic_a=topic_a,
            topic_b=topic_b,
            use_global_arguments=False,
        )

        self.status_subscription = self.create_subscription(
            RobotStatus, "/rl_deploy/status", self.status_callback, 10
        )
        self.report_publisher = self.create_publisher(String, "~/fleet_status", 10)
        self.timer = self.create_timer(0.1, self.publish_report)
        self.dashboard = DashboardServer(
            report_provider=lambda: build_fleet_report(self.fleet),
            host=str(self.get_parameter("dashboard_host").value),
            port=int(self.get_parameter("dashboard_port").value),
            web_dir=get_package_share_directory("m20_fleet_controller") + "/web",
        )
        self.dashboard.start()
        self.get_logger().info(
            f"Fleet dashboard available at http://{self.dashboard.display_host}:{self.dashboard.port}"
        )

        self.get_logger().warning(
            "READ-ONLY monitor active: controller previews are local calculations; "
            "no velocity, state, or hardware-command publisher exists."
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
        monitor.dashboard.stop()
        executor.remove_node(monitor.localization_node)
        monitor.localization_node.destroy_node()
        executor.remove_node(monitor)
        monitor.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
