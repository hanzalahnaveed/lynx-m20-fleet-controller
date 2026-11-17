"""Tests for the read-only fleet diagnostic report."""

import json
from types import SimpleNamespace

from m20_fleet_controller.fleet_manager import FleetManager
from m20_fleet_controller.fleet_report import build_fleet_report
from m20_fleet_controller.controller_core import Target


def main():
    fleet = FleetManager()
    status = SimpleNamespace(
        telemetry_fresh=True,
        command_timed_out=True,
        current_state="RLControlMode",
        safety_mode=0,
        rejected_commands=0,
    )

    # Both records are fabricated; no ROS graph or physical robot is used.
    fleet.update_status("robot_a", status, now=50.0)
    fleet.update_pose("robot_a", 1.0, 2.0, 0.25, timestamp=50.0)
    fleet.set_target("robot_a", Target(3.0, 4.0))

    report = build_fleet_report(fleet, now=50.1)
    assert report["read_only"] is True
    assert report["robots"]["robot_a"]["monitor_state"] == "observing"
    assert report["robots"]["robot_a"]["localization_fresh"] is True
    assert report["robots"]["robot_a"]["motion_enabled_in_software"] is False
    assert report["robots"]["robot_b"]["monitor_state"] == "awaiting_status"
    assert report["robots"]["robot_b"]["pose"] is None

    # Reports must be publishable as a JSON std_msgs/String payload.
    encoded = json.dumps(report, sort_keys=True)
    decoded = json.loads(encoded)
    assert decoded["robots"]["robot_a"]["pose"]["x"] == 1.0

    # A status message older than the fleet timeout is not considered fresh.
    stale = build_fleet_report(fleet, now=51.0)
    assert stale["robots"]["robot_a"]["monitor_state"] == "status_stale"

    print("FLEET REPORT TEST PASSED")


if __name__ == "__main__":
    main()
