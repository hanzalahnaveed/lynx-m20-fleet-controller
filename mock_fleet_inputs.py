"""Publish fabricated status and pose inputs for two-slot monitor testing.

Publishes only /rl_deploy/status, /robot_a/pose, and /robot_b/pose.
It does not publish velocity, state, or hardware joint commands.
"""

import rclpy
from rclpy.node import Node
from drdds.msg import RobotStatus
from geometry_msgs.msg import PoseStamped


class MockFleetInputs(Node):
    def __init__(self):
        super().__init__("mock_fleet_inputs")
        self.status_pub = self.create_publisher(
            RobotStatus, "/rl_deploy/status", 10
        )
        self.pose_a_pub = self.create_publisher(
            PoseStamped, "/robot_a/pose", 10
        )
        self.pose_b_pub = self.create_publisher(
            PoseStamped, "/robot_b/pose", 10
        )
        self.timer = self.create_timer(0.1, self.publish_inputs)
        self.get_logger().warning(
            "Publishing FABRICATED two-robot test data only: "
            "/rl_deploy/status, /robot_a/pose, and /robot_b/pose. "
            "No robot command topics are used."
        )

    def make_status(self, identity, stamp, seconds):
        status = RobotStatus()
        status.header.stamp = stamp
        status.header.frame_id = "mock_sdk"
        status.robot = identity
        status.command_source = "mock_test"
        status.current_state = "RLControlMode"
        status.current_state_id = 0
        status.requested_state = "RLControlMode"
        status.requested_state_id = 0
        status.safety_mode = 0
        status.command.linear.x = 0.0
        status.command.linear.y = 0.0
        status.command.linear.z = 0.0
        status.command.angular.x = 0.0
        status.command.angular.y = 0.0
        status.command.angular.z = 0.0
        status.command_timed_out = True
        status.rejected_commands = 0
        status.command_updates = 0
        status.joint_stamp = seconds
        status.imu_stamp = seconds
        status.telemetry_fresh = True
        status.base_rpy.x = 0.0
        status.base_rpy.y = 0.0
        status.base_rpy.z = 0.0
        status.base_angular_velocity.x = 0.0
        status.base_angular_velocity.y = 0.0
        status.base_angular_velocity.z = 0.0
        return status

    @staticmethod
    def make_pose(stamp, x, y):
        pose = PoseStamped()
        pose.header.stamp = stamp
        pose.header.frame_id = "map"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 1.0
        return pose

    def publish_inputs(self):
        now = self.get_clock().now()
        stamp = now.to_msg()
        seconds = now.nanoseconds / 1_000_000_000.0

        self.status_pub.publish(
            self.make_status("MOCK_M20_A", stamp, seconds)
        )
        self.status_pub.publish(
            self.make_status("MOCK_M20_B", stamp, seconds)
        )

        self.pose_a_pub.publish(self.make_pose(stamp, 1.0, 2.0))
        self.pose_b_pub.publish(self.make_pose(stamp, 4.0, 5.0))


def main():
    rclpy.init()
    node = MockFleetInputs()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
