import json

import rclpy
from rclpy.node import Node
from drdds.msg import RobotStatus
from geometry_msgs.msg import Twist

from .fleet_manager import FleetManager
from .ros2_command import to_twist_fields


class StatusAdapter(Node):
    def __init__(self):
        super().__init__("m20_fleet_status_adapter")

        self.declare_parameter("robot_name_map", "{}")
        raw_map = self.get_parameter("robot_name_map").value
        self.robot_name_map = json.loads(raw_map)

        if not isinstance(self.robot_name_map, dict):
            raise ValueError("robot_name_map must be a JSON object")

        self.fleet = FleetManager()

        self.subscription = self.create_subscription(
            RobotStatus,
            "/rl_deploy/status",
            self.status_callback,
            10,
        )

        self.timer = self.create_timer(0.1, self.prepare_commands)

        self.get_logger().info(
            f"Read-only status adapter started. Robot map: {self.robot_name_map}"
        )

    def status_callback(self, msg):
        robot_id = self.robot_name_map.get(msg.robot)

        if robot_id not in self.fleet.robots:
            self.get_logger().warning(
                f"Ignoring unknown robot name: {msg.robot}"
            )
            return

        self.fleet.update_status(robot_id, msg)

    def prepare_commands(self):
        for robot_id in self.fleet.robots:
            command = self.fleet.calculate(robot_id)

            # Create a Twist in memory only. No publisher exists.
            twist = Twist()
            fields = to_twist_fields(command)

            twist.linear.x = fields["linear"]["x"]
            twist.linear.y = fields["linear"]["y"]
            twist.linear.z = fields["linear"]["z"]
            twist.angular.x = fields["angular"]["x"]
            twist.angular.y = fields["angular"]["y"]
            twist.angular.z = fields["angular"]["z"]


def main(args=None):
    rclpy.init(args=args)
    node = StatusAdapter()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
