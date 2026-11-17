import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from tf_transformations import euler_from_quaternion

from .fleet_manager import FleetManager


class LocalizationAdapter(Node):
    def __init__(self, fleet, topic_a=None, topic_b=None):
        super().__init__("m20_fleet_localization_adapter")

        self.fleet = fleet

        self.declare_parameter("robot_a_pose_topic", "/robot_a/pose")
        self.declare_parameter("robot_b_pose_topic", "/robot_b/pose")

        if topic_a is None:
            topic_a = self.get_parameter("robot_a_pose_topic").value
        if topic_b is None:
            topic_b = self.get_parameter("robot_b_pose_topic").value

        self.sub_a = self.create_subscription(
            PoseStamped,
            topic_a,
            lambda msg: self.pose_callback("robot_a", msg),
            10,
        )

        self.sub_b = self.create_subscription(
            PoseStamped,
            topic_b,
            lambda msg: self.pose_callback("robot_b", msg),
            10,
        )

        self.get_logger().info(f"Robot A pose topic: {topic_a}")
        self.get_logger().info(f"Robot B pose topic: {topic_b}")

    def pose_callback(self, robot_id, msg):
        position = msg.pose.position
        orientation = msg.pose.orientation

        quaternion = [
            orientation.x,
            orientation.y,
            orientation.z,
            orientation.w,
        ]

        if not all(math.isfinite(v) for v in (
            position.x, position.y, *quaternion
        )):
            self.get_logger().warning(
                f"Ignoring invalid pose for {robot_id}"
            )
            return

        if sum(v * v for v in quaternion) < 1e-12:
            self.get_logger().warning(
                f"Ignoring zero quaternion for {robot_id}"
            )
            return

        _, _, yaw = euler_from_quaternion(quaternion)

        try:
            self.fleet.update_pose(
                robot_id,
                position.x,
                position.y,
                yaw,
            )
        except ValueError as exc:
            self.get_logger().warning(str(exc))


def main(args=None):
    rclpy.init(args=args)

    from .fleet_manager import FleetManager
    fleet = FleetManager()

    node = LocalizationAdapter(fleet)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
