"""Print one complete fleet diagnostic report from the ROS 2 topic."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ReportReader(Node):
    def __init__(self):
        super().__init__("fleet_report_reader")
        self.subscription = self.create_subscription(
            String,
            "/m20_fleet_monitor/fleet_status",
            self.callback,
            10,
        )

    def callback(self, message):
        print(json.dumps(json.loads(message.data), indent=2))
        rclpy.shutdown()


def main():
    rclpy.init()
    node = ReportReader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
