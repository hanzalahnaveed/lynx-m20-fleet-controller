from types import SimpleNamespace

from m20_fleet_controller.controller_core import Target
from m20_fleet_controller.fleet_manager import FleetManager


def make_status(telemetry_fresh=True, safety_mode=0):
    return SimpleNamespace(
        telemetry_fresh=telemetry_fresh,
        command_timed_out=True,
        current_state="RLControlMode",
        safety_mode=safety_mode,
        rejected_commands=0,
    )


def main():
    fleet = FleetManager()
    fleet.update_pose("robot_a", 0.0, 0.0, 0.0, timestamp=10.0)
    fleet.update_status("robot_a", make_status(), now=10.0)
    fleet.set_target("robot_a", Target(1.0, 0.0))
    fleet.enable_motion("robot_a", now=10.0)
    assert fleet.safety.states["robot_a"].motion_enabled

    # Missing/stale localization must both zero output and disable the gate.
    command = fleet.calculate("robot_a", now=11.0)
    assert (command.forward, command.sideways, command.yaw_rate) == (0.0, 0.0, 0.0)
    assert not fleet.safety.states["robot_a"].motion_enabled

    # Re-enable with fresh inputs, then inject an SDK safety fault.
    fleet.update_pose("robot_a", 0.0, 0.0, 0.0, timestamp=12.0)
    fleet.update_status("robot_a", make_status(), now=12.0)
    fleet.enable_motion("robot_a", now=12.0)
    fleet.update_status("robot_a", make_status(safety_mode=1), now=12.1)
    assert not fleet.safety.states["robot_a"].motion_enabled
    command = fleet.calculate("robot_a", now=12.1)
    assert (command.forward, command.sideways, command.yaw_rate) == (0.0, 0.0, 0.0)

    # Stale telemetry must also disable the gate.
    fleet.update_status("robot_a", make_status(telemetry_fresh=False), now=13.0)
    assert not fleet.safety.states["robot_a"].motion_enabled
    print("FAIL-CLOSED SAFETY TEST PASSED")


if __name__ == "__main__":
    main()
