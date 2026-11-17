from types import SimpleNamespace

from m20_fleet_controller.fleet_manager import FleetManager
from m20_fleet_controller.controller_core import Target

fleet = FleetManager()

fleet.update_pose("robot_a", 0.0, 0.0, 0.0, timestamp=100.0)
fleet.update_pose("robot_b", 2.0, 2.0, 1.57, timestamp=100.0)

fleet.set_target("robot_a", Target(1.0, 0.0))
fleet.set_target("robot_b", Target(2.0, 3.0))

fleet.set_connected("robot_a", True)
fleet.set_connected("robot_b", True)

mock_status = SimpleNamespace(
    telemetry_fresh=True,
    command_timed_out=True,
    current_state="RLControlMode",
    safety_mode=0,
    rejected_commands=0,
)

for robot_id in ("robot_a", "robot_b"):
    fleet.update_status(robot_id, mock_status, now=100.1)

print("A before enable:", fleet.calculate("robot_a", now=100.1))
print("B before enable:", fleet.calculate("robot_b", now=100.1))

fleet.enable_motion("robot_a", now=100.1)
fleet.enable_motion("robot_b", now=100.1)

print("A after enable:", fleet.calculate("robot_a", now=100.1))
print("B after enable:", fleet.calculate("robot_b", now=100.1))

print("A with stale pose:", fleet.calculate("robot_a", now=101.0))

fleet.disable_motion("robot_b")
print("B after disable:", fleet.calculate("robot_b", now=100.1))

print("A snapshot:", fleet.snapshot("robot_a", now=100.1))
print("FLEET TEST PASSED")
