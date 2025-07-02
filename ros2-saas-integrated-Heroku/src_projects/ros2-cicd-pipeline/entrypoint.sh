#!/bin/bash
set -e

# Default ROS_DISTRO if not set externally (e.g., by Dockerfile ENV)
ROS_DISTRO=${ROS_DISTRO:-jazzy}

# Default APP_HOME if not set externally
APP_HOME=${APP_HOME:-/opt/ros_app}

# Source ROS environment and local workspace
if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  echo "Sourced ROS ${ROS_DISTRO} global setup."
else
  echo "Error: ROS global setup file not found at /opt/ros/${ROS_DISTRO}/setup.bash" >&2
  # exit 1 # Or try to continue if local_setup might be enough for some cases
fi

if [ -f "${APP_HOME}/install/local_setup.bash" ]; then
  source "${APP_HOME}/install/local_setup.bash"
  echo "Sourced application local_setup.bash from ${APP_HOME}/install."
else
  echo "Warning: Application local_setup.bash not found at ${APP_HOME}/install/local_setup.bash." >&2
  echo "This might be okay if your application doesn't have a colcon workspace or it's not populated." >&2
fi

echo "Container entrypoint script finished sourcing setup files."
echo "Executing command: $@"
echo "---------------------------------------------------"

# Execute the command passed to `docker run` (which will be the CMD from Dockerfile if not overridden)
exec "$@"
