from types import SimpleNamespace

from m20_fleet_controller.ros2_status_adapter import StatusAdapter

adapter = StatusAdapter.__new__(StatusAdapter)
adapter.robot_name_map = {"M20": "robot_a"}

from m20_fleet_controller.fleet_manager import FleetManager
adapter.fleet = FleetManager()

msg = SimpleNamespace(
    robot="M20",
    telemetry_fresh=True,
    command_timed_out=True,
    current_state="RLControlMode",
    safety_mode=0,
    rejected_commands=0,
)

adapter.status_callback(msg)

robot = adapter.fleet.robots["robot_a"]

assert robot.status_received
assert robot.telemetry_fresh
assert robot.connected

print("Mock status accepted:", robot.name)
print("Connected:", robot.connected)
print("Telemetry fresh:", robot.telemetry_fresh)
print("Status received:", robot.status_received)
print("MOTION ENABLED:", adapter.fleet.safety.states["robot_a"].motion_enabled)
print("READ-ONLY ADAPTER TEST PASSED")
