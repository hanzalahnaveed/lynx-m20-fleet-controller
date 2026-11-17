from dataclasses import dataclass


@dataclass
class SafetyState:
    connected: bool = False
    motion_enabled: bool = False


class SafetyGate:
    def __init__(self):
        self.states = {
            "robot_a": SafetyState(),
            "robot_b": SafetyState(),
        }

    def set_connected(self, robot_id, connected):
        self._get_state(robot_id).connected = bool(connected)

    def enable_motion(self, robot_id):
        state = self._get_state(robot_id)
        if not state.connected:
            raise RuntimeError("Cannot enable motion: robot is not connected")
        state.motion_enabled = True

    def disable_motion(self, robot_id):
        self._get_state(robot_id).motion_enabled = False

    def allow_command(self, robot_id, pose_is_fresh):
        state = self._get_state(robot_id)
        return (
            state.connected
            and state.motion_enabled
            and pose_is_fresh
        )

    def _get_state(self, robot_id):
        if robot_id not in self.states:
            raise ValueError(f"Unknown robot ID: {robot_id}")
        return self.states[robot_id]
