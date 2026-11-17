# Hardware Readiness Checklist (Physical Integration Deferred)

This checklist records what must be verified before any physical robot communication or motion. The current repository remains a read-only monitor with dry-run previews. Completing this document does not authorize hardware command publishing.

## Confirmed in software-only development

- [x] ROS 2 Humble development workspace on Ubuntu 22.04 x86_64.
- [x] DEEP Robotics SDK packages built in the development workspace.
- [x] Read-only fleet monitor subscribes to `/rl_deploy/status`.
- [x] Per-robot pose subscriptions are configurable.
- [x] Mock two-robot status and pose integration works.
- [x] Missing/stale localization is reported and produces zero preview.
- [x] Software motion gate is disabled by default.
- [x] No velocity, state-command, or hardware-joint publisher exists in the fleet monitor.

## Required when robots become available

### Robot identity and firmware

- [ ] Record serial number and physical label for each unit.
- [ ] Record firmware version for each unit.
- [ ] Confirm required firmware version with DEEP Robotics documentation/support.
- [ ] Obtain and securely handle the unique SDK authorization code for each unit.
- [ ] Observe the actual `RobotStatus.robot` value from each unit independently.
- [ ] Confirm the two identity strings are distinct and stable across reconnects.
- [ ] Configure `robot_name_map` only from observed values; never infer identity from slot order.

### Network and DDS isolation

- [ ] Record each robot's IP, subnet, gateway, Wi-Fi/Ethernet mode, and host reachability.
- [ ] Confirm which machine runs the SDK process and which DDS implementation/configuration it uses.
- [ ] Inspect the actual SDK DDS domain configuration on both robots.
- [ ] Prove that each host SDK process receives only its intended robot telemetry.
- [ ] Prove that a command/test participant on one domain cannot reach the other robot.
- [ ] Do not treat ROS namespaces as isolation: SDK hardware topics are absolute (for example `/JOINTS_CMD`).
- [ ] Document a recovery procedure if the two robots appear in the same DDS domain.

### Read-only telemetry commissioning

- [ ] Start with one robot and a physically safe, stationary setup.
- [ ] Verify status topic type, QoS compatibility, identity, update rate, and timestamps.
- [ ] Verify joint, IMU, and battery telemetry freshness against actual data.
- [ ] Confirm disconnect/reconnect and stale-data reporting.
- [ ] Repeat independently for the second robot.
- [ ] Run both read-only monitors only after identity and DDS isolation are demonstrated.
- [ ] Confirm the monitor remains free of command publishers.

### Localization commissioning

- [ ] Select and document the localization source for each robot.
- [ ] Confirm both poses use the same world coordinate frame.
- [ ] Confirm metres, radians, yaw convention, timestamps, and frame IDs.
- [ ] Measure localization update rate and latency.
- [ ] Test missing, stale, discontinuous, and invalid poses.
- [ ] Confirm pose-to-robot association independently for each unit.

### Separate safety review before any future command integration

- [ ] Obtain the manufacturer's operating and emergency-stop procedure.
- [ ] Identify a physical emergency stop independent of this software.
- [ ] Document safe startup, shutdown, recovery, and operator roles.
- [ ] Verify SDK constructor/startup side effects before running any deployment executable.
- [ ] Verify how the robot is physically stopped; do not assume process exit or zero Twist is an emergency stop.
- [ ] Review command timeout, state transitions, safety modes, and fault recovery.
- [ ] Design single-robot commissioning first; do not start with simultaneous two-robot motion.
- [ ] Perform an independent code and safety review before adding any command publisher.

## Known SDK integration hazards from source inspection

- The SDK hardware interface uses absolute topics including `/JOINTS_CMD`, `/JOINTS_DATA`, `/IMU_DATA`, and `/BATTERY_DATA`.
- The inspected `DdsInterface` constructor publishes low-level joint-control messages as part of its initialization sequence.
- `M20Interface::Start()` resets position offsets and publishes a joint command.
- `M20Interface::Stop()` was empty in the inspected source; process shutdown must not be treated as a verified physical stop.
- The inspected SDK source did not establish unique physical identity strings for two units.
- A separate DDS-domain example in the SDK README was under simulation guidance; physical-robot domain isolation must be verified independently.

## Release gate

Physical command integration remains blocked until identity, DDS isolation, telemetry, localization, firmware/authorization, and physical emergency-stop procedures have all been verified and documented. The read-only monitor can continue to be developed and tested without a robot.
