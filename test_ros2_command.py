from m20_fleet_controller.controller_core import VelocityCommand
from m20_fleet_controller.ros2_command import (
    to_twist_fields,
    zero_twist_fields,
)

command = VelocityCommand(
    forward=0.2,
    sideways=0.1,
    yaw_rate=0.3,
)

print("Converted command:")
print(to_twist_fields(command))

print("Zero command:")
print(zero_twist_fields())

try:
    to_twist_fields(VelocityCommand(forward=float("nan")))
except ValueError as error:
    print("Invalid command rejected:", error)
