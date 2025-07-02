#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Environment Setup ---
echo "DigitalOcean Docker Entrypoint Script"
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
if [ -f "${ROS_WORKSPACE}/install/local_setup.bash" ]; then
  source "${ROS_WORKSPACE}/install/local_setup.bash"
  echo "Sourced local ROS workspace setup from ${ROS_WORKSPACE}/install."
else
  echo "Info: Local ROS workspace setup not found or workspace not built at ${ROS_WORKSPACE}/install."
fi

# --- Service Management ---
# This entrypoint can use Supervisor or run services directly.
# For simplicity here, we'll show direct startup. Supervisor is good for production.

# Start Nginx
echo "Starting Nginx..."
# Ensure Nginx config is correctly linked if not done in Dockerfile
if [ ! -L /etc/nginx/sites-enabled/default ] && [ -f /etc/nginx/sites-available/default ]; then
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
fi
nginx -g "daemon off;" & # Run Nginx in the foreground (managed by Docker/Supervisor)
NGINX_PID=$!
echo "Nginx started with PID ${NGINX_PID}"

# Start Node.js backend (example)
# This assumes your Node.js app's package.json has a "start" script.
# The actual Node.js app code should be copied/mounted into ${APP_ROOT}/backend or similar.
NODE_APP_DIR="${APP_ROOT}/backend" # Adjust if your Node.js app is elsewhere
if [ -f "${NODE_APP_DIR}/package.json" ]; then
  echo "Starting Node.js backend from ${NODE_APP_DIR}..."
  cd "${NODE_APP_DIR}"
  # Check for node_modules, run npm install if not present (might be slow on startup)
  # if [ ! -d "node_modules" ]; then
  #   echo "node_modules not found, running npm install..."
  #   npm install --production
  # fi
  # npm start & # Start in background
  # Or, if you have a specific server file:
  # node server.js &
  # NODE_PID=$!
  # echo "Node.js backend started with PID ${NODE_PID}"
  # For this example, we assume the Node.js app is started via a different mechanism
  # or by a supervisor. If this script is the main process manager, uncomment and adapt.
  echo "Node.js backend should be started by a process manager (like Supervisor) or run manually after container start."
  echo "To start it manually (example): cd ${NODE_APP_DIR} && npm start"
else
  echo "Warning: Node.js application not found at ${NODE_APP_DIR}/package.json. Backend will not be started by this script."
fi
cd "${APP_ROOT}" # Return to APP_ROOT

# Start ROS application (example: a launch file)
# This is highly dependent on what the user wants to run.
# Example:
# if [ -f "${ROS_WORKSPACE}/install/setup.bash" ]; then # Check if workspace was built
#   echo "Starting ROS application (example)..."
#   # Ensure DISPLAY is set if GUI tools like RViz/Gazebo client are launched
#   # export DISPLAY=:0 # This needs an X server, often handled via VNC/X11 forwarding
#   # ros2 launch my_package my_application.launch.py &
#   # ROS_APP_PID=$!
#   # echo "ROS application started with PID ${ROS_APP_PID}"
#   echo "ROS application components should be launched as needed (e.g., via Supervisor or manually)."
# else
#   echo "ROS workspace not built, skipping ROS application auto-start."
# fi


# --- Keep container running / Wait for processes ---
# If not using a process manager like Supervisor, and you started background jobs,
# you need a way to keep the entrypoint script (and thus the container) running
# and handle graceful shutdown.

echo "---------------------------------------------------------------------"
echo "ROS2 SaaS Environment Initialized."
echo " - Nginx is running (PID ${NGINX_PID}). Frontend on port 80."
echo " - Node.js backend should be running (if configured to auto-start)."
echo " - ROS components can be launched from within this container."
echo "   Example: ros2 launch <your_pkg> <your_launch_file.py>"
echo "   Or run Gazebo: gazebo ${ROS_WORKSPACE}/src/turtlebot3_simulations/turtlebot3_gazebo/worlds/turtlebot3_world.world"
echo "---------------------------------------------------------------------"

# If Nginx is the only critical foreground process started by this script:
wait $NGINX_PID

# If you have multiple background processes started by this script and no supervisor:
# trap "echo 'Stopping services...'; kill $NGINX_PID $NODE_PID $ROS_APP_PID; exit 0" SIGINT SIGTERM
# while true; do
#   # Check if critical processes are alive, or just sleep
#   # Example: if ! kill -0 $NGINX_PID 2>/dev/null; then echo "Nginx died"; exit 1; fi
#   sleep 1
# done

# If this script is just for initial setup and `CMD ["bash"]` is used in Dockerfile,
# then this script will execute and exit, leaving you in a bash shell.
# If `CMD` is for supervisor, then this script might not be the final ENTRYPOINT,
# or it would `exec supervisord`.

# For the current Dockerfile setup (CMD ["bash"]), this script will run, print messages,
# start Nginx in the background, and then the CMD ["bash"] will take over,
# providing an interactive shell. Nginx will continue running.
# This is okay for development/testing. For production, a process manager is better.

# If Nginx is run in foreground (`daemon off;`), this script will block on `nginx`
# until Nginx stops or is killed. This is a common pattern for single-process containers.
# If you need Node.js and Nginx and ROS nodes, Supervisor is a good choice.
# The provided Dockerfile has `CMD ["bash"]`, so this script will start nginx in the background
# and then drop to bash.

# If the Dockerfile's CMD was `CMD ["/entrypoint_do.sh"]` and this script was meant to be the main process
# then the `wait $NGINX_PID` or the `while true; do sleep 1; done` loop would be essential.
# Given `CMD ["bash"]` in Dockerfile, this script mainly serves as an initializer.
# To make it a long-running script that manages nginx:
# (In Dockerfile: `ENTRYPOINT ["/entrypoint_do.sh"]`, `CMD []` or `CMD ["nginx-foreground"]` if this script handles it)
# If this script is the *only* thing that runs (via ENTRYPOINT and no CMD or CMD that is an arg to this script):
# exec nginx -g "daemon off;" # This makes Nginx the main process, script ends.

# For the current setup (Dockerfile CMD ["bash"], ENTRYPOINT ["/entrypoint_do.sh"]):
# Nginx is started in the background. The script will finish, then bash starts.
# This is fine for a dev setup.
# If you want this script to be the one that keeps the container alive via Nginx:
# 1. Dockerfile: `ENTRYPOINT ["/entrypoint_do.sh"]`, `CMD ["nginx-foreground"]` (or similar marker)
# 2. This script:
#    if [ "$1" = "nginx-foreground" ]; then
#        echo "Starting Nginx in foreground..."
#        exec nginx -g "daemon off;"
#    else
#        # Original logic for interactive/other modes
#        echo "Entrypoint finished. Handing over to Docker CMD: $@"
#        exec "$@"
#    fi
# For simplicity now, it starts nginx in background and relies on subsequent CMD.

# If the Docker CMD is just "bash", this script runs, starts nginx in background, then exits.
# The container continues with bash. Nginx keeps running.
# This is often how dev containers are set up.
# If you want Nginx to be THE process that keeps container alive, use `exec nginx -g "daemon off;"` at the end.
# For now, let's assume the `CMD ["bash"]` from Dockerfile is for development interaction.
# The `nginx -g "daemon off;" &` starts it, and it will run until container stops.

# To ensure the script doesn't exit immediately if it's the *only* thing run by ENTRYPOINT with no CMD:
if [ "$#" -eq 0 ] || ( [ "$#" -eq 1 ] && [ "$1" = "bash" ] ); then
    # If no args passed to entrypoint, or only "bash" (from Dockerfile CMD)
    # We need to keep the script alive if it's managing background services
    # and is the primary process.
    # However, with `CMD ["bash"]` in Dockerfile, this entrypoint effectively just initializes.
    # The `nginx -g "daemon off;" &` is key.
    # If you were to `docker run <image>` (no command), this entrypoint runs, then bash runs.
    # If `docker run <image> some_other_command`, entrypoint runs, then `some_other_command` runs.
    echo "Entrypoint initialization complete. Container will now proceed with Docker CMD or further commands."
fi

# If this script is meant to be the main long-running process (e.g. Dockerfile CMD is empty or calls this)
# and you are not using a process manager like supervisor, you'd need a loop like:
# while true; do sleep 1000; done
# Or, as mentioned, `wait $NGINX_PID` if Nginx is the primary service started here in foreground.
# Given current Dockerfile (CMD ["bash"]), this script's backgrounding of Nginx is fine.
# The script will finish, and the bash shell will start, with Nginx running.
# This is suitable for a development/interactive setup on the droplet.
# For a production setup, `supervisord` would be launched by the CMD/Entrypoint.

# No `exec "$@"` here if we want Nginx to stay in background and then drop to bash via Dockerfile CMD.
# If this script *was* the final command (e.g. Dockerfile CMD was empty or an arg for this script
# to start services in foreground), then `exec "$@"` or `wait` would be at the end.
# With `CMD ["bash"]`, this script finishes, nginx is in bg, bash starts.
```

This `entrypoint_do.sh` script:
-   Sets up and sources the ROS environment.
-   Starts Nginx in the background (suitable for a `CMD ["bash"]` scenario where Nginx continues running after the script exits and bash starts).
-   Includes commented-out placeholders for starting a Node.js backend and ROS applications, suggesting these would typically be managed by a process manager like Supervisor or run manually.
-   Provides informational messages about the environment.

The script is designed to be flexible. If used with `CMD ["bash"]` in the Dockerfile (as it currently is), it initializes services that can run in the background and then drops the user into a shell. If the Dockerfile's `CMD` were changed to run `supervisord`, this entrypoint might do less, or `supervisord` would be the main command.

This script, along with the Dockerfile and nginx.conf, provides a good base for the DigitalOcean deployment. The `setup_droplet.sh` will tie these together with the droplet provisioning.
