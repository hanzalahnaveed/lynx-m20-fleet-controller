from setuptools import find_packages, setup
from glob import glob
import os

package_name = "m20_fleet_controller"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test*"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [os.path.join("resource", package_name)]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "config"), glob("*.yaml")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Lynx M20 Fleet Controller Maintainer",
    maintainer_email="maintainer@example.com",
    description="Read-only ROS 2 fleet monitor and dry-run controller previews.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "m20_fleet_monitor = m20_fleet_controller.ros2_fleet_monitor:main",
            "m20_fleet_status_adapter = m20_fleet_controller.ros2_status_adapter:main",
            "m20_fleet_localization_adapter = m20_fleet_controller.ros2_localization_adapter:main",
        ],
    },
)
