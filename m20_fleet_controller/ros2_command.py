import math

from .controller_core import VelocityCommand


def to_twist_fields(command):
    values = (
        command.forward,
        command.sideways,
        command.yaw_rate,
    )

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Velocity command contains a non-finite value")

    return {
        "linear": {
            "x": float(command.forward),
            "y": float(command.sideways),
            "z": 0.0,
        },
        "angular": {
            "x": 0.0,
            "y": 0.0,
            "z": float(command.yaw_rate),
        },
    }


def zero_twist_fields():
    return to_twist_fields(VelocityCommand())
