from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    default_params = PathJoinSubstitution([
        FindPackageShare("m20_fleet_controller"),
        "config",
        "default_monitor_params.yaml",
    ])
    return LaunchDescription([
        DeclareLaunchArgument(
            "dashboard_host", default_value="127.0.0.1",
            description="Dashboard bind address; keep loopback unless using a trusted network",
        ),
        DeclareLaunchArgument(
            "dashboard_port", default_value="8765",
            description="Local browser dashboard HTTP port",
        ),
        DeclareLaunchArgument(
            "params_file",
            default_value=default_params,
            description="ROS 2 parameter YAML for the read-only fleet monitor",
        ),
        Node(
            package="m20_fleet_controller",
            executable="m20_fleet_monitor",
            name="m20_fleet_monitor",
            output="screen",
            parameters=[LaunchConfiguration("params_file"), {
                "dashboard_host": LaunchConfiguration("dashboard_host"),
                "dashboard_port": LaunchConfiguration("dashboard_port"),
            }],
        ),
    ])
