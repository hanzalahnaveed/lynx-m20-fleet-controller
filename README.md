# Lynx M20 Fleet Controller

Read-only host-side software for monitoring two logical DEEP Robotics Lynx M20 robot slots using ROS 2.

## Current milestone: read-only fleet monitor with controller previews

`m20_fleet_controller.ros2_fleet_monitor` combines the SDK status subscription and both localization subscriptions in one process and one shared `FleetManager`. It publishes a JSON diagnostic report as `std_msgs/msg/String` on `/m20_fleet_monitor/fleet_status`.

The report includes status freshness, telemetry freshness, localization freshness, current SDK state, safety mode, command timeout flag, rejected-command count, latest pose, target, and a local controller preview.

The preview is a dry-run calculation only. It does not enable the software safety gate, update the active command, publish velocity, or send hardware commands. Preview values are not approved for physical use.

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

Targets are configurable parameters. Defaults for the software preview are Robot A (2.0, 2.0) metres and Robot B (4.0, 6.0) metres:

```bash
-p robot_a_target_x:=2.0 -p robot_a_target_y:=2.0 \
-p robot_b_target_x:=4.0 -p robot_b_target_y:=6.0
```

In another terminal, inspect the report:

```bash
source /opt/ros/humble/setup.bash
python3 ~/lynx_ws/fleet_controller/read_fleet_report.py
```

The two pose topics must provide `geometry_msgs/msg/PoseStamped` in the same world coordinate frame, with metres and a consistent yaw convention.

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

The dedicated dry-run controller test is:

```bash
python3 test_controller_preview.py
```

Tests use fabricated messages and poses. They do not connect to a robot.

## Safety boundary

- This repository is not approved for physical robot control.
- Do not run the SDK `rl_deploy` executable as part of these tests.
- The monitor creates a diagnostic report publisher only. It does not publish `cmd_vel`, state commands, or `/JOINTS_CMD`.
- Controller previews do not enable the safety gate or update the active command.
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


## Install as a ROS 2 Python package

This repository is an `ament_python` package. Keep the repository at `~/lynx_ws/fleet_controller`. Build it from the workspace root by adding that repository as an additional colcon base path (no copy or symlink is needed):

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws
colcon build --base-paths src fleet_controller --packages-select m20_fleet_controller
source install/setup.bash
```

Verify the package and executable:

```bash
ros2 pkg list | grep '^m20_fleet_controller

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

Expected: both slots report fresh status, telemetry, and localization with `monitor_state: observing`; their fabricated poses are different. Both remain `motion_enabled_in_software: false`.

## Localization-loss mock test

Keep the monitor running. Stop the normal mock publisher with Ctrl+C, then restart it with robot B pose publishing disabled:

```bash
python3 mock_fleet_inputs.py --ros-args -p publish_robot_b_pose:=false
```

Expected after the pose freshness timeout: Robot A remains `observing`; Robot B has fresh status and telemetry but `localization_fresh: false`, `pose: null`, and `monitor_state: awaiting_localization`. Both remain `motion_enabled_in_software: false`.

## Controller preview test

The monitor assigns configurable targets and reports candidate velocities calculated independently for each robot. These values are dry-run previews only; the safety gate remains disabled and no command publisher exists.

With the mock monitor and mock input publisher running, read the report. Expected default targets and previews:

- Robot A pose (1, 2), target (2, 2): forward preview 0.2 m/s, sideways 0.0 m/s, yaw rate 0.0 rad/s.
- Robot B pose (4, 5), target (4, 6): forward preview 0.15 m/s, sideways preview 0.15 m/s, yaw rate 0.3 rad/s.

If localization becomes stale, that robot's preview returns zero. Both robots must continue to report `motion_enabled_in_software: false`.

For a deterministic unit test, run `python3 test_controller_preview.py`. It uses fabricated inputs and does not start ROS or communicate with hardware.

ros2 pkg executables m20_fleet_controller
```

Run the read-only monitor using the installed console entry point:

```bash
ros2 run m20_fleet_controller m20_fleet_monitor --ros-args \\
  --params-file ~/lynx_ws/fleet_controller/mock_monitor_params.yaml
```

The mock input publisher remains a separate test helper and can still be run with `python3 mock_fleet_inputs.py` from the repository root. The monitor entry point does not add a velocity, state, or hardware-command publisher. It only subscribes to SDK status and pose inputs and publishes the diagnostic fleet report.

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

Expected: both slots report fresh status, telemetry, and localization with `monitor_state: observing`; their fabricated poses are different. Both remain `motion_enabled_in_software: false`.

## Localization-loss mock test

Keep the monitor running. Stop the normal mock publisher with Ctrl+C, then restart it with robot B pose publishing disabled:

```bash
python3 mock_fleet_inputs.py --ros-args -p publish_robot_b_pose:=false
```

Expected after the pose freshness timeout: Robot A remains `observing`; Robot B has fresh status and telemetry but `localization_fresh: false`, `pose: null`, and `monitor_state: awaiting_localization`. Both remain `motion_enabled_in_software: false`.

## Controller preview test

The monitor assigns configurable targets and reports candidate velocities calculated independently for each robot. These values are dry-run previews only; the safety gate remains disabled and no command publisher exists.

With the mock monitor and mock input publisher running, read the report. Expected default targets and previews:

- Robot A pose (1, 2), target (2, 2): forward preview 0.2 m/s, sideways 0.0 m/s, yaw rate 0.0 rad/s.
- Robot B pose (4, 5), target (4, 6): forward preview 0.15 m/s, sideways preview 0.15 m/s, yaw rate 0.3 rad/s.

If localization becomes stale, that robot's preview returns zero. Both robots must continue to report `motion_enabled_in_software: false`.

For a deterministic unit test, run `python3 test_controller_preview.py`. It uses fabricated inputs and does not start ROS or communicate with hardware.
