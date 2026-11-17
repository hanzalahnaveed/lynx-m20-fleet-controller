"""Pure-Python diagnostic report builder for the two-robot fleet."""


def _robot_report(fleet, robot_id, now=None):
    snapshot = fleet.snapshot(robot_id, now=now)
    pose = snapshot["pose"]
    target = snapshot["target"]

    if not snapshot["status_fresh"]:
        monitor_state = "awaiting_status" if not snapshot["connected"] else "status_stale"
    elif not snapshot["telemetry_fresh"]:
        monitor_state = "telemetry_stale"
    elif pose is None:
        monitor_state = "awaiting_localization"
    elif snapshot["safety_mode"] != 0:
        monitor_state = "safety_mode_active"
    else:
        monitor_state = "observing"

    return {
        "monitor_state": monitor_state,
        "connected": snapshot["connected"],
        "status_fresh": snapshot["status_fresh"],
        "telemetry_fresh": snapshot["telemetry_fresh"],
        "localization_fresh": pose is not None,
        "motion_enabled_in_software": snapshot["motion_enabled"],
        "current_state": snapshot["current_state"],
        "safety_mode": snapshot["safety_mode"],
        "command_timed_out": snapshot["command_timed_out"],
        "rejected_commands": snapshot["rejected_commands"],
        "pose": (
            {"x": pose.x, "y": pose.y, "yaw": pose.yaw}
            if pose is not None else None
        ),
        "target": (
            {"x": target.x, "y": target.y}
            if target is not None else None
        ),
    }


def build_fleet_report(fleet, now=None):
    """Return JSON-serializable diagnostic state; never a movement command.

    "observing" means only that recent status, telemetry, and localization
    are present and SDK safety_mode is zero. It is not a motion-safety claim.
    """
    return {
        "read_only": True,
        "robots": {
            robot_id: _robot_report(fleet, robot_id, now=now)
            for robot_id in ("robot_a", "robot_b")
        },
    }
