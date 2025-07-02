#!/bin/bash
set -e

# Source ROS 2 setup
source /opt/ros/${ROS_DISTRO}/setup.bash
if [ -f /ros2_ws/install/setup.bash ]; then
  source /ros2_ws/install/setup.bash
fi

exec "$@"
