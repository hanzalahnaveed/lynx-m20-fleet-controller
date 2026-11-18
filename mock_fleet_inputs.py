"""Publish fabricated, moving two-robot inputs for dashboard testing.

Publishes only /rl_deploy/status, /robot_a/pose, and /robot_b/pose.
It never publishes velocity, state, or hardware joint commands.

Set animate_poses:=false for stationary test positions, or
publish_robot_b_pose:=false to simulate loss of Robot B localization.
"""
import math

import rclpy
from rclpy.node import Node
from drdds.msg import RobotStatus
from geometry_msgs.msg import PoseStamped


class MockFleetInputs(Node):
    def __init__(self):
        super().__init__("mock_fleet_inputs")
        self.declare_parameter("publish_robot_b_pose", True)
        self.declare_parameter("animate_poses", True)
        self.declare_parameter("trajectory_radius", 1.0)
        self.declare_parameter("trajectory_period", 24.0)
        self.publish_robot_b_pose = bool(
            self.get_parameter("publish_robot_b_pose").value
        )
        self.animate_poses = bool(self.get_parameter("animate_poses").value)
        self.radius = float(self.get_parameter("trajectory_radius").value)
        self.period = float(self.get_parameter("trajectory_period").value)
        if not math.isfinite(self.radius) or self.radius <= 0.05:
            raise ValueError("trajectory_radius must be finite and greater than 0.05")
        if not math.isfinite(self.period) or self.period < 2.0:
            raise ValueError("trajectory_period must be finite and at least 2 seconds")
        self.started_at = self.get_clock().now().nanoseconds / 1e9

        self.status_pub = self.create_publisher(RobotStatus, "/rl_deploy/status", 10)
        self.pose_a_pub = self.create_publisher(PoseStamped, "/robot_a/pose", 10)
        self.pose_b_pub = self.create_publisher(PoseStamped, "/robot_b/pose", 10)
        self.timer = self.create_timer(0.1, self.publish_inputs)
        self.get_logger().warning(
            "Publishing FABRICATED two-robot data. Animated poses: "
            f"{self.animate_poses}; Robot B pose: {self.publish_robot_b_pose}. "
            "Only /rl_deploy/status and pose topics are used; no robot command "
            "topics are published."
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
    def make_pose(stamp, x, y, yaw):
        pose = PoseStamped()
        pose.header.stamp = stamp
        pose.header.frame_id = "map"
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def pose_for_robot(self, elapsed, phase, center_x, center_y):
        if not self.animate_poses:
            return center_x, center_y, 0.0
        omega = 2.0 * math.pi / self.period
        angle = omega * elapsed + phase
        x = center_x + self.radius * math.cos(angle)
        y = center_y + 0.65 * self.radius * math.sin(angle)
        yaw = math.atan2(
            -0.65 * self.radius * omega * math.cos(angle),
            -self.radius * omega * math.sin(angle),
        )
        return x, y, yaw

    def publish_inputs(self):
        now = self.get_clock().now()
        stamp = now.to_msg()
        seconds = now.nanoseconds / 1_000_000_000.0
        elapsed = seconds - self.started_at

        self.status_pub.publish(self.make_status("MOCK_M20_A", stamp, seconds))
        self.status_pub.publish(self.make_status("MOCK_M20_B", stamp, seconds))

        a = self.pose_for_robot(elapsed, 0.0, 1.0, 2.0)
        b = self.pose_for_robot(elapsed, math.pi, 4.0, 5.0)
        self.pose_a_pub.publish(self.make_pose(stamp, *a))
        if self.publish_robot_b_pose:
            self.pose_b_pub.publish(self.make_pose(stamp, *b))


def main():
    rclpy.init()
    node = MockFleetInputs()
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
