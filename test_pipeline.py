from types import SimpleNamespace

from m20_fleet_controller.fleet_manager import FleetManager
from m20_fleet_controller.controller_core import Target
from m20_fleet_controller.ros2_command import (
    to_twist_fields,
    zero_twist_fields,
)

fleet = FleetManager()

# Fabricated localization data for software testing only.
fleet.update_pose("robot_a", 0.0, 0.0, 0.0, timestamp=100.0)
fleet.update_pose("robot_b", 2.0, 2.0, 1.57, timestamp=100.0)

fleet.set_target("robot_a", Target(1.0, 0.0))
fleet.set_target("robot_b", Target(2.0, 3.0))

fleet.set_connected("robot_a", True)
fleet.set_connected("robot_b", True)

# Fabricated fresh status; no robot or hardware connection is involved.
mock_status = SimpleNamespace(
    telemetry_fresh=True,
    command_timed_out=True,
    current_state="RLControlMode",
    safety_mode=0,
    rejected_commands=0,
)

for robot_id in ("robot_a", "robot_b"):
    fleet.update_status(robot_id, mock_status, now=100.1)

# Both robots must be stopped before explicit enablement.
for robot_id in ("robot_a", "robot_b"):
    command = fleet.calculate(robot_id, now=100.1)
    assert command.forward == 0.0
    assert command.sideways == 0.0
    assert command.yaw_rate == 0.0
    print(robot_id, "blocked:", zero_twist_fields())

# Enable each robot independently.
fleet.enable_motion("robot_a", now=100.1)
fleet.enable_motion("robot_b", now=100.1)

for robot_id in ("robot_a", "robot_b"):
    command = fleet.calculate(robot_id, now=100.1)
    fields = to_twist_fields(command)
    print(robot_id, "enabled command:", fields)

# Stale localization must produce a zero Twist.
stale_command = fleet.calculate("robot_a", now=101.0)
assert stale_command.forward == 0.0
assert stale_command.sideways == 0.0
assert stale_command.yaw_rate == 0.0
assert not fleet.safety.states["robot_a"].motion_enabled
print("robot_a stale localization:", to_twist_fields(stale_command))

# Disabling Robot B must produce a zero Twist.
fleet.disable_motion("robot_b")
disabled_command = fleet.calculate("robot_b", now=100.1)
assert disabled_command.forward == 0.0
assert disabled_command.sideways == 0.0
assert disabled_command.yaw_rate == 0.0
print("robot_b disabled:", to_twist_fields(disabled_command))

print("PIPELINE TEST PASSED")
