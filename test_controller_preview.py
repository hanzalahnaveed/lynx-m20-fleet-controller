from types import SimpleNamespace

from m20_fleet_controller.controller_core import Target
from m20_fleet_controller.fleet_manager import FleetManager
from m20_fleet_controller.fleet_report import build_fleet_report

fleet = FleetManager()
mock_status = SimpleNamespace(
    telemetry_fresh=True,
    command_timed_out=True,
    current_state="RLControlMode",
    safety_mode=0,
    rejected_commands=0,
)

# Fabricated data only. The safety gate deliberately remains disabled.
fleet.update_pose("robot_a", 1.0, 2.0, 0.0, timestamp=100.0)
fleet.update_pose("robot_b", 4.0, 5.0, 0.0, timestamp=100.0)
fleet.update_status("robot_a", mock_status, now=100.1)
fleet.update_status("robot_b", mock_status, now=100.1)

fleet.set_target("robot_a", Target(2.0, 2.0))
fleet.set_target("robot_b", Target(4.0, 6.0))

report = build_fleet_report(fleet, now=100.1)

for robot_id in ("robot_a", "robot_b"):
    item = report["robots"][robot_id]
    assert item["preview_only"] is True
    assert item["motion_enabled_in_software"] is False
    assert item["preview_velocity"] != {
        "forward": 0.0, "sideways": 0.0, "yaw_rate": 0.0
    }
    print(robot_id, item["target"], item["preview_velocity"])

# Simulate Robot B localization becoming stale.
stale_report = build_fleet_report(fleet, now=101.0)
robot_b = stale_report["robots"]["robot_b"]
assert robot_b["localization_fresh"] is False
assert robot_b["preview_velocity"] == {
    "forward": 0.0, "sideways": 0.0, "yaw_rate": 0.0
}
assert robot_b["motion_enabled_in_software"] is False
print("robot_b stale localization preview:", robot_b["preview_velocity"])
print("CONTROLLER PREVIEW TEST PASSED")
