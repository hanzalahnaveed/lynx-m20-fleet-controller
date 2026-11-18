"""Publish fabricated robot data and simulate following dashboard destinations."""
import math
import rclpy
from rclpy.node import Node
from drdds.msg import RobotStatus
from geometry_msgs.msg import Point, PoseStamped

class MockFleetInputs(Node):
    def __init__(self):
        super().__init__("mock_fleet_inputs")
        self.declare_parameter("publish_robot_b_pose", True)
        self.declare_parameter("mock_speed", 0.35)
        self.publish_b=bool(self.get_parameter("publish_robot_b_pose").value)
        self.speed=float(self.get_parameter("mock_speed").value)
        if not math.isfinite(self.speed) or not 0 < self.speed <= 1:
            raise ValueError("mock_speed must be between 0 and 1 m/s")
        self.poses={"robot_a":[0.6,2.6,0.0],"robot_b":[4.4,4.4,0.0]}
        self.targets={"robot_a":[2.0,2.0],"robot_b":[4.0,6.0]}
        self.status_pub=self.create_publisher(RobotStatus,"/rl_deploy/status",10)
        self.pose_pubs={"robot_a":self.create_publisher(PoseStamped,"/robot_a/pose",10),
                        "robot_b":self.create_publisher(PoseStamped,"/robot_b/pose",10)}
        self.create_subscription(Point,"/m20_fleet_monitor/robot_a_target",lambda m:self.set_target("robot_a",m),10)
        self.create_subscription(Point,"/m20_fleet_monitor/robot_b_target",lambda m:self.set_target("robot_b",m),10)
        self.timer=self.create_timer(0.1,self.publish_inputs)
        self.get_logger().warning("SIMULATION ONLY: markers move toward dashboard destinations. No robot command topics are published.")
    def set_target(self,robot,msg):
        if math.isfinite(msg.x) and math.isfinite(msg.y): self.targets[robot]=[msg.x,msg.y]
    @staticmethod
    def status(identity,stamp,seconds):
        m=RobotStatus(); m.header.stamp=stamp; m.header.frame_id="mock_sdk"
        m.robot=identity; m.command_source="mock_test"; m.current_state="RLControlMode"
        m.requested_state="RLControlMode"; m.safety_mode=0; m.command_timed_out=True
        m.joint_stamp=seconds; m.imu_stamp=seconds; m.telemetry_fresh=True
        return m
    @staticmethod
    def pose_msg(stamp,x,y,yaw):
        m=PoseStamped(); m.header.stamp=stamp; m.header.frame_id="map"
        m.pose.position.x=x; m.pose.position.y=y
        m.pose.orientation.z=math.sin(yaw/2); m.pose.orientation.w=math.cos(yaw/2)
        return m
    def move(self,robot):
        p=self.poses[robot]; t=self.targets[robot]
        dx,dy=t[0]-p[0],t[1]-p[1]; d=math.hypot(dx,dy)
        if d>0.03:
            step=min(d,self.speed*0.1); p[0]+=dx/d*step; p[1]+=dy/d*step
            p[2]=math.atan2(dy,dx)
    def publish_inputs(self):
        now=self.get_clock().now(); stamp=now.to_msg(); sec=now.nanoseconds/1e9
        for robot,identity in (("robot_a","MOCK_M20_A"),("robot_b","MOCK_M20_B")):
            self.status_pub.publish(self.status(identity,stamp,sec))
            if robot=="robot_b" and not self.publish_b: continue
            self.move(robot); self.pose_pubs[robot].publish(self.pose_msg(stamp,*self.poses[robot]))

def main():
    rclpy.init(); node=MockFleetInputs()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()
if __name__=="__main__": main()
