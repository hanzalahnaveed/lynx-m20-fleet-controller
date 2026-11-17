# Lynx M20 Fleet Controller

Read-only host-side software for monitoring two logical DEEP Robotics Lynx M20 robot slots using ROS 2.

## Current milestone: read-only fleet monitor

`m20_fleet_controller.ros2_fleet_monitor` combines the SDK status subscription and both localization subscriptions in one process and one shared `FleetManager`. It publishes a JSON diagnostic report as `std_msgs/msg/String` on `/m20_fleet_monitor/fleet_status`.

The report includes status freshness, telemetry freshness, localization freshness, current SDK state, safety mode, command timeout flag, rejected-command count, and the latest pose.

Possible `monitor_state` values are `awaiting_status`, `status_stale`, `telemetry_stale`, `awaiting_localization`, `safety_mode_active`, and `observing`. `observing` means only that the expected recent input data exists and the SDK safety mode is zero. It is **not** a statement that motion is safe or enabled.

## Run in the Ubuntu 22.04 / ROS 2 Humble development VM

Source ROS and the SDK workspace overlays that provide `drdds.msg.RobotStatus`, then run from the repository root:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
PYTHONPATH="$PWD:$PYTHONPATH" python3 -m m20_fleet_controller.ros2_fleet_monitor --ros-args \
  -p robot_name_map:='{"SDK_ROBOT_NAME":"robot_a"}' \
  -p robot_a_pose_topic:=/robot_a/pose \
  -p robot_b_pose_topic:=/robot_b/pose
```

Replace `SDK_ROBOT_NAME` only with an identity string verified from the actual status message. The SDK source inspected so far does not establish distinct identity strings for two physical M20 units. Do not guess or map the same identity to both slots.

In another terminal, inspect the report:

```bash
source /opt/ros/humble/setup.bash
ros2 topic echo /m20_fleet_monitor/fleet_status
```

The two pose topics are configurable. They must provide `geometry_msgs/msg/PoseStamped` in the same world coordinate frame, with metres and a consistent yaw convention.

## Run software-only tests

With ROS 2, the SDK message package, and `tf_transformations` available:

```bash
cd ~/lynx_ws/fleet_controller
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
for test in test_*.py; do
  echo "===== $test ====="
  python3 "$test" || exit 1
done
```

Tests use fabricated messages and poses. They do not connect to a robot.

## Safety boundary

- This repository is not approved for physical robot control.
- Do not run the SDK `rl_deploy` executable as part of these tests.
- This monitor creates a diagnostic publisher only. It does not publish `cmd_vel`, state commands, or `/JOINTS_CMD`.
- A software zero velocity value is not a verified physical emergency stop.
- SDK robot identity mapping and DDS isolation for two physical robots remain unverified.
- Firmware, authorization, network setup, and physical safe operating procedures must be verified before any hardware integration.

## Project layout

```text
m20_fleet_controller/
  controller_core.py
  fleet_manager.py
  fleet_report.py
  localization.py
  ros2_command.py
  ros2_fleet_monitor.py
  ros2_localization_adapter.py
  ros2_status_adapter.py
  safety_gate.py
test_*.py
```

## Two-robot mock monitor test

This software-only test publishes two fabricated SDK identities and two fabricated poses. It does not connect to physical robots.

Pull the latest repository changes, then start the monitor in Terminal 1:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
PYTHONPATH="$PWD:$PYTHONPATH" python3 -m m20_fleet_controller.ros2_fleet_monitor --ros-args --params-file mock_monitor_params.yaml
```

Start the fabricated input publisher in Terminal 2:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
python3 mock_fleet_inputs.py
```

Read one complete report in Terminal 3:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
python3 read_fleet_report.py
```

Expected: both slots report fresh status, telemetry, and localization with `monitor_state: observing`; their fabricated poses are different. Both remain `motion_enabled_in_software: false`. These values validate message routing and report aggregation only, not physical readiness.

## Localization-loss mock test

This test verifies that localization loss is distinguished from loss of SDK status. Keep the monitor running with `mock_monitor_params.yaml`. Stop the normal mock publisher with Ctrl+C, then restart it with robot B pose publishing disabled:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
python3 mock_fleet_inputs.py --ros-args -p publish_robot_b_pose:=false
```

Read the report:

```bash
python3 read_fleet_report.py
```

Expected after the pose freshness timeout: robot A remains `observing`; robot B has fresh status and telemetry but `localization_fresh: false`, `pose: null`, and `monitor_state: awaiting_localization`. Both remain `motion_enabled_in_software: false`. This is a fabricated software test only.
