#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Environment Setup ---
echo "AWS EC2/ECS Docker Entrypoint Script"
echo "Timestamp: $(date)"

ROS_DISTRO=${ROS_DISTRO:-jazzy}
APP_ROOT=${APP_ROOT:-/opt/ros2_saas_app}
ROS_WORKSPACE=${ROS_WORKSPACE:-${APP_ROOT}/colcon_ws}

echo "ROS_DISTRO: ${ROS_DISTRO}"
echo "APP_ROOT: ${APP_ROOT}"
echo "ROS_WORKSPACE: ${ROS_WORKSPACE}"

# Source ROS environment
if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  echo "Sourced ROS ${ROS_DISTRO} global setup."
else
  echo "Warning: ROS global setup file not found at /opt/ros/${ROS_DISTRO}/setup.bash"
fi

# Source local ROS workspace if it exists and has been built
# This workspace is expected to be populated during the Docker image build process.
if [ -f "${ROS_WORKSPACE}/install/local_setup.bash" ]; then
  source "${ROS_WORKSPACE}/install/local_setup.bash"
  echo "Sourced local ROS workspace setup from ${ROS_WORKSPACE}/install."
else
  echo "Info: Local ROS workspace setup not found or workspace not built at ${ROS_WORKSPACE}/install."
  echo "Ensure your ROS application was built and its install space is at ${ROS_WORKSPACE}/install."
fi

# --- Application Startup Logic ---
# This section should be customized based on how your application is structured
# and what services need to run (e.g., ROS nodes, Node.js backend, Nginx).

# Example: Start a Node.js backend application
# Assumes Node.js app is in ${APP_ROOT}/backend and has a start script in package.json
NODE_BACKEND_DIR="${APP_ROOT}/backend"
if [ -f "${NODE_BACKEND_DIR}/package.json" ]; then
  echo "Starting Node.js backend from ${NODE_BACKEND_DIR}..."
  cd "${NODE_BACKEND_DIR}"
  # Run in the background. For ECS, you'd typically define this as a separate container
  # or ensure it's properly managed if multiple processes run in one container.
  # Using `npm start &` is simple but not robust for production without a process manager.
  npm start &
  NODE_PID=$!
  echo "Node.js backend started with PID ${NODE_PID} (running in background)."
  cd "${APP_ROOT}" # Return to app root
else
  echo "Warning: Node.js backend (package.json) not found at ${NODE_BACKEND_DIR}. Not starting."
fi

# Example: Start Nginx (if you're serving frontend from this container)
# Assumes Nginx is installed and configured (e.g., via a custom nginx.conf copied in Dockerfile)
# if command -v nginx &> /dev/null; then
#   echo "Starting Nginx..."
#   nginx -g "daemon off;" & # Or use supervisord to manage it
#   NGINX_PID=$!
#   echo "Nginx started with PID ${NGINX_PID} (running in background)."
# else
#   echo "Info: Nginx not found or not configured to start."
# fi


# Example: Launch a ROS2 application
# This is highly specific to your application.
# You might launch a specific launch file.
# For ECS, long-running ROS nodes are part of the task.
# Ensure that if you launch ROS nodes, their lifecycle is managed.
# For example, if this is the main container for an ECS task,
# the ROS application might be the primary process.

# If this container is meant to run a specific ROS launch file as its main task:
# CMD_ARG="$1" # First argument passed to the entrypoint (from Docker CMD or ECS task definition command)
# if [ -n "${CMD_ARG}" ] && [ "${CMD_ARG}" != "bash" ]; then
#   echo "Executing command passed from Docker CMD/ECS: ${CMD_ARG} $@"
#   exec "$@" # Execute the command from Docker CMD or ECS task definition
# else
#   # Default behavior if no specific command is given, or if it's just "bash"
#   echo "No specific ROS command provided to entrypoint. Starting default services (if any) or an interactive shell."
#   # Example: Launch a default ROS application component
#   # if [ -f "${ROS_WORKSPACE}/install/local_setup.bash" ]; then
#   #   echo "Launching default ROS application component..."
#   #   exec ros2 launch your_main_package your_main_launch.launch.py
#   # else
#   #   echo "ROS workspace not found or not built. Cannot launch default ROS component."
#   # fi
# fi


echo "---------------------------------------------------------------------"
echo "AWS EC2/ECS Application Environment Initialized."
echo " - Node.js backend attempts to start if found at ${NODE_BACKEND_DIR}."
echo " - Other services (Nginx, specific ROS nodes) should be configured"
echo "   either in this script, via a process manager (like Supervisor),"
echo "   or through ECS task definition commands."
echo " "
echo "If CMD was 'bash' or no command was given, an interactive shell will start."
echo "To launch ROS components manually (example):"
echo "  ros2 launch <your_pkg> <your_launch_file.py>"
echo "  gazebo ${ROS_WORKSPACE}/install/<some_pkg>/share/<some_pkg>/worlds/my_world.world"
echo "---------------------------------------------------------------------"

# If the Docker CMD is "bash" or empty, this script will execute, start background tasks (like Node.js),
# and then `exec "$@"` will typically execute `bash` (the default CMD).
# If ECS overrides the CMD to run a specific ROS launch file, `exec "$@"` will run that.

# If this script is intended to be the main long-running process that keeps the container alive
# (e.g., by running a primary application in the foreground), then the `exec "$@"` is crucial.
# If all your main tasks are backgrounded here (like `npm start &`),
# then you need a foreground process to keep the container alive, e.g.:
# tail -f /dev/null
# Or, better, use a process manager like `supervisor`.

# For now, assume `exec "$@"` will run the CMD from Dockerfile or ECS task definition.
# If that CMD is `bash`, you get a shell. If it's `ros2 launch ...`, that will run.
exec "$@"
```

This `entrypoint_aws.sh` script:
-   Sources the ROS global and local workspace setups.
-   Includes an example of how to start a Node.js backend application (assuming it's located at `${APP_ROOT}/backend` and managed by `npm start`). This is run in the background.
-   Includes commented-out examples for starting Nginx and a generic ROS application. The actual services to start would depend heavily on the specific application being deployed.
-   The script finishes with `exec "$@"`, which means it will execute the command passed to the Docker container (the `CMD` from the Dockerfile, or the command specified in an ECS Task Definition). This makes it flexible. If the `CMD` is `bash`, an interactive shell starts. If the `CMD` is `ros2 launch my_pkg my_launch.py`, that launch file will be executed as the main process of the container.

This setup is geared towards flexibility for AWS deployments, whether on a single EC2 instance (where `bash` might be a useful default `CMD` for interaction) or on ECS (where the `CMD` would typically be the primary application process, like a `ros2 launch` command).

Next, I'll make this script executable and then create the CloudFormation template and the GitHub Actions workflow for ECR.
