#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Environment Setup ---
echo "GCP (GKE/Cloud Run) Docker Entrypoint Script"
echo "Timestamp: $(date)"

ROS_DISTRO=${ROS_DISTRO:-jazzy}
APP_ROOT=${APP_ROOT:-/opt/ros2_saas_app}
ROS_WORKSPACE=${ROS_WORKSPACE:-${APP_ROOT}/colcon_ws}
# PORT is often injected by Cloud Run, or defined in K8s service. Default to 8080 if not set.
# Your application inside the container (Node.js, Nginx) must listen on this $PORT.
PORT=${PORT:-8080}


echo "ROS_DISTRO: ${ROS_DISTRO}"
echo "APP_ROOT: ${APP_ROOT}"
echo "ROS_WORKSPACE: ${ROS_WORKSPACE}"
echo "Application will listen on PORT: ${PORT}" # Informational

# Source ROS environment
if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  echo "Sourced ROS ${ROS_DISTRO} global setup."
else
  echo "Warning: ROS global setup file not found at /opt/ros/${ROS_DISTRO}/setup.bash"
fi

# Source local ROS workspace if it exists and has been built
# This workspace is expected to be populated during the Docker image build process (e.g., by Cloud Build).
if [ -f "${ROS_WORKSPACE}/install/local_setup.bash" ]; then
  source "${ROS_WORKSPACE}/install/local_setup.bash"
  echo "Sourced local ROS workspace setup from ${ROS_WORKSPACE}/install."
else
  echo "Info: Local ROS workspace setup not found or workspace not built at ${ROS_WORKSPACE}/install."
  echo "Ensure your ROS application was built and its install space is at ${ROS_WORKSPACE}/install within the image."
fi

# --- Application Startup Logic ---
# This section should be customized based on your application structure.
# It might start a Node.js server, Nginx, or directly a ROS2 launch file.
# The command executed here is often determined by the `CMD` or `args` in your Kubernetes manifest or Cloud Run service definition.

# Example: Start a Node.js backend application
# Assumes Node.js app is in ${APP_ROOT}/backend and its server.js is configured to listen on $PORT
NODE_BACKEND_DIR="${APP_ROOT}/backend"
if [ -f "${NODE_BACKEND_DIR}/server.js" ] && [ -f "${NODE_BACKEND_DIR}/package.json" ]; then
  echo "Starting Node.js backend from ${NODE_BACKEND_DIR} to listen on PORT: ${PORT}..."
  cd "${NODE_BACKEND_DIR}"
  # Modify server.js or pass PORT to make Express listen on the correct port.
  # `npm start` should ideally respect the PORT environment variable.
  # This will become the main process if not backgrounded.
  # For Kubernetes, you usually want one main foreground process per container.
  exec npm start # Assumes 'start' script in package.json runs `node server.js` and respects PORT
  # Or: exec node server.js # If server.js directly listens on process.env.PORT
elif [ "$1" == "run_node_backend" ]; then # Allow explicit command
  echo "Explicitly starting Node.js backend on PORT: ${PORT}..."
  cd "${NODE_BACKEND_DIR}"
  exec npm start
fi


# Example: Start Nginx (if serving frontend and Nginx is configured to listen on $PORT)
# if command -v nginx &> /dev/null && [ "$1" == "run_nginx" ]; then
#   echo "Starting Nginx to listen on PORT: ${PORT}..."
#   # Ensure nginx.conf is updated to listen on $PORT or uses a variable that can be set.
#   # This typically involves modifying /etc/nginx/sites-available/default or a similar conf file.
#   # sed -i "s/listen 80;/listen ${PORT};/" /etc/nginx/sites-available/default # Example modification
#   exec nginx -g "daemon off;"
# fi


# Example: Launch a ROS2 application directly (if this container's main purpose)
# if [ "$1" == "launch_ros_app" ] && [ -f "${ROS_WORKSPACE}/install/local_setup.bash" ]; then
#   echo "Launching main ROS application..."
#   # shift # consume "launch_ros_app"
#   # exec ros2 launch your_package your_launch_file.launch.py "$@" # Pass remaining args
#   exec ros2 launch your_main_package your_main_launch.launch.py
# fi


echo "---------------------------------------------------------------------"
echo "GCP Application Environment Initialized."
echo "Entrypoint script finished."
echo "---------------------------------------------------------------------"

# If none of the above `exec` commands were hit (e.g., due to missing files or conditions not met),
# this script will proceed to execute the command passed as arguments to it (from Docker CMD or K8s manifest).
# This allows flexibility, e.g., `CMD ["bash"]` in Dockerfile gives a shell if no other primary process started.
# Or `CMD ["my_custom_script.sh"]` in Dockerfile.
# Or K8s `args: ["ros2", "launch", "my_pkg", "my_launch.py"]`

if [ "$#" -gt 0 ]; then
    echo "Executing command from Docker CMD / K8s args: $@"
    exec "$@"
else
    # Default behavior if no CMD/args from K8s and no specific condition above was met
    echo "No specific command to run. Falling back to bash for interactive debugging."
    echo "This container might not be serving any application if not configured via K8s manifest or Docker CMD."
    exec bash
fi
```

This `entrypoint_gcp.sh` script:
-   Sets up and sources the ROS environment.
-   Is designed to be flexible for GKE/Cloud Run:
    -   It checks for a `PORT` environment variable (commonly injected by Cloud Run, or can be set in K8s) and defaults to `8080`. The application inside (e.g., Node.js server) **must** be configured to listen on this `$PORT`.
    -   It includes an example of how to start a Node.js backend using `npm start`, assuming the `server.js` is configured to use `process.env.PORT`. This is run with `exec` to make it the main process of the container if this path is taken.
    -   It includes commented-out placeholders for starting Nginx or a ROS2 launch file directly.
    -   The final `exec "$@"` allows the `CMD` from the Dockerfile or `command` and `args` from a Kubernetes manifest to define the primary process for the container. If no specific command is provided and no internal condition starts a process with `exec`, it defaults to `bash`.

This script ensures that whatever application component is intended to run (Node.js backend, Nginx, ROS launch file) becomes the main foreground process, which is standard practice for containers managed by orchestrators like Kubernetes.

Next, I will make this script executable and then create the Kubernetes manifests and Cloud Build configuration.
