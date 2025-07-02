# Dockerfile for DigitalOcean Deployment
# This Dockerfile sets up a ROS2 Jazzy environment with Gazebo and Node.js.
# It's intended to be run on a DigitalOcean droplet that has Docker installed.

# --- Base Image: ROS2 Jazzy with Gazebo ---
# Using an image that includes ROS desktop and Gazebo tools.
# You could also start from ros:jazzy-ros-base and install gazebo_ros_pkgs manually.
FROM ros:jazzy-desktop-full

LABEL maintainer="Your Name <user@todo.todo>"
LABEL description="ROS2 Jazzy with Gazebo, Node.js, and Nginx for DigitalOcean."

ENV ROS_DISTRO=jazzy
ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_VISIBLE_DEVICES \
    ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES \
    ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,utility,compute

# --- System Updates and Essential Packages ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    gnupg \
    lsb-release \
    # Python tools (already largely present in ros-desktop, but ensure pip)
    python3-pip \
    python3-venv \
    python3-colcon-common-extensions \
    python3-rosdep \
    # Nginx for serving frontend
    nginx \
    # Supervisor for process management (optional, but good for running multiple services)
    supervisor \
    # Terminator (optional, for a better terminal experience if accessing GUI)
    terminator \
    # Mesa utils for GLX (especially if running GUI apps like Gazebo client without NVIDIA)
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# --- Node.js Installation ---
# Install Node.js (e.g., LTS version, currently 20.x, or 18.x for wider compatibility)
# Using NodeSource repository for up-to-date versions
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
# Verify Node.js installation
RUN node -v && npm -v

# --- ROS2 Workspace and Application Setup ---
# Create a directory for the ROS workspace and application code
# The setup_droplet.sh script will handle cloning/copying user's ROS projects here.
ENV APP_ROOT=/opt/ros2_saas_app
ENV ROS_WORKSPACE=${APP_ROOT}/colcon_ws
RUN mkdir -p ${ROS_WORKSPACE}/src
RUN mkdir -p ${APP_ROOT}/frontend
RUN mkdir -p ${APP_ROOT}/nginx_config
RUN mkdir -p /var/log/supervisor # For supervisor logs

WORKDIR ${APP_ROOT}

# --- Nginx Configuration ---
# Copy custom Nginx configuration.
# This will be created in the repository and copied here.
# The setup_droplet.sh script might also place it or link it.
COPY nginx.conf /etc/nginx/sites-available/default
# COPY nginx.conf ${APP_ROOT}/nginx_config/default.conf
# RUN ln -sf ${APP_ROOT}/nginx_config/default.conf /etc/nginx/sites-available/default
# RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
# Ensure default Nginx welcome page is disabled if it exists
RUN rm -f /etc/nginx/sites-enabled/default

# --- Supervisor Configuration (Optional) ---
# If using supervisor to manage Nginx, ROS nodes, Node.js backend.
# COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# Example supervisord.conf content would be:
# [program:nginx]
# command=/usr/sbin/nginx -g "daemon off;"
# autostart=true
# autorestart=true
# ... other programs for ROS launch files, Node.js server ...

# --- Application Code ---
# The actual ROS packages and Node.js backend code will be mounted or copied
# into this image by the user or deployment scripts on the DigitalOcean droplet.
# This Dockerfile primarily sets up the environment.
# For example, the user would clone their main app repo into ${ROS_WORKSPACE}/src
# and their Node.js backend into a directory like ${APP_ROOT}/backend.
# The ros2-front-end (index.html) would be copied to ${APP_ROOT}/frontend.

# Example placeholder for Node.js backend (if it's part of this image build)
# WORKDIR ${APP_ROOT}/backend
# COPY ./backend_src/package.json ./backend_src/package-lock.json* ./
# RUN npm install --production
# COPY ./backend_src/ .
# WORKDIR ${APP_ROOT} # Return to app root

# --- ROS Environment Sourcing ---
# Add sourcing to .bashrc so it's available in interactive shells
# And ensure entrypoint/CMD scripts also source it.
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
RUN echo "if [ -f ${ROS_WORKSPACE}/install/local_setup.bash ]; then source ${ROS_WORKSPACE}/install/local_setup.bash; fi" >> ~/.bashrc
RUN echo "export APP_ROOT=${APP_ROOT}" >> ~/.bashrc
RUN echo "export ROS_WORKSPACE=${ROS_WORKSPACE}" >> ~/.bashrc

# --- Ports ---
EXPOSE 80   # Nginx HTTP
EXPOSE 443  # Nginx HTTPS (if configured)
EXPOSE 3000 # Node.js backend (if it runs on this port and isn't proxied by Nginx)
# EXPOSE 11311 # ROS Master (ROS1 legacy, not for ROS2 default DDS)
# EXPOSE 9090 # rosbridge_server (if used)

# --- Entrypoint/CMD ---
# The entrypoint can be a script that initializes things and starts services.
# For DigitalOcean, you might run this container and then exec into it,
# or have it start Supervisor, or a custom script.
COPY entrypoint_do.sh /entrypoint_do.sh
RUN chmod +x /entrypoint_do.sh

ENTRYPOINT ["/entrypoint_do.sh"]
# CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"] # If using Supervisor
CMD ["bash"] # Default to bash for interactive use or if entrypoint handles startup

# --- Build Instructions (Informational) ---
# To build this Docker image:
# 1. Ensure `nginx.conf` and `entrypoint_do.sh` are in the same directory as this Dockerfile.
# 2. Run: `docker build -t ros2-saas-digitalocean .`

# --- Usage on DigitalOcean Droplet ---
# 1. Provision a Ubuntu 24.04 droplet with Docker installed.
# 2. SSH into the droplet.
# 3. Clone your application repository which contains this Dockerfile and related configs.
# 4. Build the Docker image (as above) or pull a pre-built one.
# 5. Run the Docker container:
#    docker run -d -p 80:80 -p 443:443 \
#      --name ros2_saas_app \
#      -v /path/to/your/cloned/ros_workspace_src:${ROS_WORKSPACE}/src \
#      -v /path/to/your/cloned/frontend_files:${APP_ROOT}/frontend \
#      -v /path/to/your/cloned/backend_files:${APP_ROOT}/backend \
#      # Add -v /dev/dri:/dev/dri for GPU access to host (Mesa) if needed
#      # For NVIDIA GPU: --gpus all (requires nvidia-docker2 on host)
#      ros2-saas-digitalocean
#
#    The volumes would map your actual project code into the container.
#    The `setup_droplet.sh` script will automate much of this.
```

This Dockerfile:
- Starts from `ros:jazzy-desktop-full` to get ROS2 and Gazebo tools.
- Installs Nginx for serving the frontend and Node.js for the backend.
- Sets up directories for the application, ROS workspace, frontend, and Nginx config.
- Includes placeholders for copying `nginx.conf` and an `entrypoint_do.sh` script (which I'll create next).
- Sources ROS environment in `.bashrc`.
- Exposes common ports.
- Defines an `ENTRYPOINT` and default `CMD`.
- Contains informational notes on building and running.

Next, I will create `nginx.conf` and `entrypoint_do.sh`.
