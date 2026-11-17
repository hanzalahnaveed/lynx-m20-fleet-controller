"""Pure-Python diagnostic report builder for the two-robot fleet."""

import time


def _robot_report(fleet, robot_id, now=None):
    if now is None:
        now = time.monotonic()

    snapshot = fleet.snapshot(robot_id, now=now)
    slot = fleet.robots[robot_id]
    pose = snapshot["pose"]
    target = snapshot["target"]
    preview = fleet.preview_calculate(robot_id, now=now)
    status_age = now - slot.last_status_time
    status_message_fresh = (
        slot.status_received
        and 0 <= status_age <= fleet.status_timeout
    )

    if not slot.status_received:
        monitor_state = "awaiting_status"
    elif not status_message_fresh:
        monitor_state = "status_stale"
    elif not slot.telemetry_fresh:
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
        "status_received": slot.status_received,
        "status_fresh": status_message_fresh,
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
        "preview_velocity": {
            "forward": preview.forward,
            "sideways": preview.sideways,
            "yaw_rate": preview.yaw_rate,
        },
        "preview_only": True,
    }


def build_fleet_report(fleet, now=None):
    """Return JSON-serializable diagnostics and dry-run calculations.

    Preview velocity is calculated locally and is never published. "observing"
    is not a motion-safety claim.
    """
    return {
        "read_only": True,
        "robots": {
            robot_id: _robot_report(fleet, robot_id, now=now)
            for robot_id in ("robot_a", "robot_b")
        },
    }
