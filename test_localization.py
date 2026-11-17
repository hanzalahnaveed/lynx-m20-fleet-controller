from m20_fleet_controller.localization import LocalizationStore

store = LocalizationStore(max_age=0.25)

store.update("robot_a", 1.0, 2.0, 0.5, timestamp=100.0)
store.update("robot_b", 3.0, 4.0, 1.0, timestamp=100.0)

print("Fresh Robot A:", store.get_pose("robot_a", now=100.1))
print("Fresh Robot B:", store.get_pose("robot_b", now=100.1))

print("Stale Robot A:", store.get_pose("robot_a", now=101.0))

try:
    store.update("robot_a", float("nan"), 2.0, 0.5, timestamp=100.1)
except ValueError as error:
    print("Invalid pose rejected:", error)
