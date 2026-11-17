# Lynx M20 Fleet Controller

Read-only host-side ROS 2 software for monitoring two logical DEEP Robotics Lynx M20 robot slots and calculating dry-run target velocity previews.

**Current status:** software-only monitoring and preview prototype. Physical robot integration is deferred because the robots are not currently available. The fleet monitor has no velocity, state-command, or hardware-joint publisher.

## Implemented

- ROS 2 Humble / Ubuntu 22.04 package structure (`ament_python`).
- One fleet monitor process with a shared fleet manager.
- Two independently tracked logical robot slots.
- SDK status subscription on `/rl_deploy/status`.
- Configurable `PoseStamped` inputs for each robot.
- Status, telemetry, and localization freshness checks.
- Target-based body-frame velocity previews with configurable limits.
- JSON diagnostic report on `/m20_fleet_monitor/fleet_status`.
- Software safety gate that starts disabled and fails closed on stale status, missing/stale localization, stale telemetry, or nonzero SDK safety mode.
- Mock two-robot and localization-loss integration helpers.

## Build and install

The checkout is expected at `~/lynx_ws/fleet_controller`. Build it alongside the SDK workspace:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws
colcon build --base-paths src fleet_controller --packages-select m20_fleet_controller
source install/setup.bash
ros2 pkg list | grep '^m20_fleet_controller$'
ros2 pkg executables m20_fleet_controller
```

## Fleet dashboard

The monitor serves a browser dashboard from the same read-only process. It polls the local HTTP endpoint for the latest JSON fleet report; it has no motion controls and cannot command either robot.

After building and launching the monitor, open `http://127.0.0.1:8765` in a browser on the Ubuntu VM. The default bind address is loopback-only. To expose the dashboard on the VM network, set `dashboard_host` to `0.0.0.0` in a trusted network and configure the VM firewall accordingly. Do not expose it to the public internet.

The dashboard shows each robot slot, status/telemetry/localization freshness, current state, safety mode, pose, target, and locally calculated preview velocity. It displays `awaiting_status` until a verified identity map is configured.

## Run the read-only monitor

The installed default parameter file deliberately has an empty `robot_name_map`. That prevents unverified SDK identities from being assigned to either robot slot.

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
source ~/lynx_ws/install/setup.bash
ros2 launch m20_fleet_controller m20_fleet_monitor.launch.py
```

For mock testing, use the mock parameter file instead:

```bash
ros2 launch m20_fleet_controller m20_fleet_monitor.launch.py \
  params_file:=/home/ubuntu/lynx_ws/fleet_controller/mock_monitor_params.yaml
```

The monitor publishes only the diagnostic report. It does not publish `cmd_vel`, state commands, or `/JOINTS_CMD`.

## Run the two-robot mock integration

Terminal 1 — start monitor with mock identity mapping:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
source ~/lynx_ws/install/setup.bash
ros2 launch m20_fleet_controller m20_fleet_monitor.launch.py \
  params_file:=/home/ubuntu/lynx_ws/fleet_controller/mock_monitor_params.yaml
```

Terminal 2 — publish fabricated status and pose inputs:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
python3 mock_fleet_inputs.py
```

Terminal 3 — read one report:

```bash
source /opt/ros/humble/setup.bash
python3 ~/lynx_ws/fleet_controller/read_fleet_report.py
```

Expected: both slots have fresh status, telemetry, and localization; both have `monitor_state: observing`; both have `motion_enabled_in_software: false`.

### Localization-loss test

Stop the mock publisher and restart it without Robot B's pose:

```bash
python3 mock_fleet_inputs.py --ros-args -p publish_robot_b_pose:=false
```

Expected after the pose freshness timeout: Robot A remains `observing`; Robot B reports `awaiting_localization`, `localization_fresh: false`, `pose: null`, and a zero preview.

## Targets and controller previews

Default targets are Robot A (2.0, 2.0) metres and Robot B (4.0, 6.0) metres. They can be overridden at launch:

```bash
ros2 launch m20_fleet_controller m20_fleet_monitor.launch.py \
  params_file:=/home/ubuntu/lynx_ws/fleet_controller/mock_monitor_params.yaml
```

For direct parameter overrides, use ROS arguments with the executable or adapt a YAML file. Preview velocities are calculations only, not commands sent to a robot.

## Run software-only tests

Source ROS and the SDK overlay first:

```bash
source /opt/ros/humble/setup.bash
source ~/lynx_ws/src/sdk_deploy/install/setup.bash
cd ~/lynx_ws/fleet_controller
bash run_software_tests.sh
```

The script sources ROS 2 Humble and the SDK overlay, then runs every `test_*.py` script and stops on the first failure. Tests use fabricated inputs. They do not connect to physical robots.

## Safety boundaries and known SDK hazards

- Do not run the SDK `rl_deploy` executable as part of software-only tests.
- The SDK hardware interface uses absolute topics including `/JOINTS_CMD`, `/JOINTS_DATA`, `/IMU_DATA`, and `/BATTERY_DATA`. ROS namespaces do not isolate these absolute topics.
- The inspected `DdsInterface` constructor publishes low-level joint-control messages during initialization.
- `M20Interface::Start()` resets position offsets and publishes a joint command.
- `M20Interface::Stop()` was empty in the inspected source. Process shutdown must not be treated as a verified physical stop.
- The inspected SDK source does not establish distinct identity strings for two physical M20 units.
- A software zero velocity is not a physical emergency stop.
- Firmware, authorization, network configuration, physical identity, DDS isolation, and emergency-stop procedures must be verified before hardware integration.

See [HARDWARE_READINESS.md](HARDWARE_READINESS.md) for the detailed physical commissioning checklist.

## Repository layout

```text
m20_fleet_controller/   core, fleet manager, ROS adapters, monitor, report
launch/                  ROS 2 launch file
resource/                ament package marker
mock_fleet_inputs.py     fabricated two-robot input publisher
mock_monitor_params.yaml mock identity mapping for tests only
default_monitor_params.yaml safe default with empty identity mapping
read_fleet_report.py     one-shot report reader
test_*.py                software-only tests
HARDWARE_READINESS.md    physical integration release checklist
```
