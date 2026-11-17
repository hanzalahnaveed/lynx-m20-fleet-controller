from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("params_file", default_value=""),
        Node(
            package="m20_fleet_controller",
            executable="m20_fleet_monitor",
            name="m20_fleet_monitor",
            output="screen",
            parameters=[LaunchConfiguration("params_file")],
        ),
    ])
