from types import SimpleNamespace

from m20_fleet_controller.fleet_manager import FleetManager
from m20_fleet_controller.ros2_localization_adapter import LocalizationAdapter

fleet = FleetManager()
adapter = LocalizationAdapter.__new__(LocalizationAdapter)
adapter.fleet = fleet

msg = SimpleNamespace(
    pose=SimpleNamespace(
        position=SimpleNamespace(x=1.5, y=2.5, z=0.0),
        orientation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
    )
)

adapter.pose_callback("robot_a", msg)

pose = fleet.localization.get_pose("robot_a")

assert pose is not None
assert abs(pose.x - 1.5) < 1e-6
assert abs(pose.y - 2.5) < 1e-6
assert abs(pose.yaw) < 1e-6

print("Robot A pose:", pose)
print("LOCALIZATION ADAPTER TEST PASSED")
