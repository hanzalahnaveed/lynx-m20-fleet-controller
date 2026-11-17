from types import SimpleNamespace

from m20_fleet_controller.controller_core import Target
from m20_fleet_controller.fleet_manager import FleetManager


fleet = FleetManager()

status = SimpleNamespace(
    telemetry_fresh=True,
    command_timed_out=True,
    current_state="rl_control",
    safety_mode=0,
    rejected_commands=0,
)

# Robot A: fresh pose and status
fleet.update_pose("robot_a", 0.0, 0.0, 0.0, timestamp=100.0)
fleet.update_status("robot_a", status, now=100.0)
fleet.set_target("robot_a", Target(1.0, 0.0))

# Robot B: no status, so it must remain blocked
fleet.update_pose("robot_b", 0.0, 0.0, 0.0, timestamp=100.0)
fleet.set_target("robot_b", Target(1.0, 0.0))

fleet.enable_motion("robot_a", now=100.1)

print("Robot A command:", fleet.calculate("robot_a", now=100.1))
print("Robot B command:", fleet.calculate("robot_b", now=100.1))

# Robot A status becomes stale
print("Robot A after stale status:", fleet.calculate("robot_a", now=101.0))
print("Robot A enabled:", fleet.snapshot("robot_a", now=101.0)["motion_enabled"])

print("STATUS INTEGRATION TEST PASSED")
