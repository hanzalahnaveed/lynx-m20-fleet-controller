from m20_fleet_controller.safety_gate import SafetyGate

gate = SafetyGate()

print("Initially blocked:",
      gate.allow_command("robot_a", True))

gate.set_connected("robot_a", True)

print("Connected but not enabled:",
      gate.allow_command("robot_a", True))

gate.enable_motion("robot_a")

print("Enabled with fresh pose:",
      gate.allow_command("robot_a", True))

print("Enabled with stale pose:",
      gate.allow_command("robot_a", False))

gate.disable_motion("robot_a")

print("After disabling:",
      gate.allow_command("robot_a", True))
