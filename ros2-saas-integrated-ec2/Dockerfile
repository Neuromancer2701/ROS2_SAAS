# Dockerfile for AWS EC2/ECS Deployment (ROS2 Jazzy, Gazebo, Node.js)
# This image can be pushed to AWS ECR and used by ECS or run on an EC2 instance.

# --- Base Image: ROS2 Jazzy with Gazebo ---
# Using an image that includes ROS desktop and Gazebo tools.
# For GPU instances (like g4dn), ensure the base image and drivers are compatible.
# NVIDIA provides NGC containers (e.g., nvcr.io/nvidia/ros:jazzy-ros-base-jammy) that can be good starting points for GPU work.
# However, for broad compatibility first, we'll use a standard ROS image.
# If using NVIDIA GPU on EC2, the host AMI (e.g., Deep Learning AMI) and nvidia-docker2 are key.
FROM ros:jazzy-desktop-full

LABEL maintainer="Your Name <user@todo.todo>"
LABEL description="ROS2 Jazzy with Gazebo, Node.js for AWS EC2/ECS deployment."

ENV ROS_DISTRO=jazzy
ENV DEBIAN_FRONTEND=noninteractive

# For GPU acceleration with NVIDIA (ensure host EC2 instance has NVIDIA drivers & nvidia-container-toolkit)
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
    python3-pip \
    python3-venv \
    python3-colcon-common-extensions \
    python3-rosdep \
    # Nginx (optional, if serving frontend directly from this container, or use ALB/CloudFront)
    # nginx \
    # Supervisor (optional, for process management if not using ECS task definitions effectively)
    # supervisor \
    terminator \
    mesa-utils \
    # AWS CLI (useful for interacting with other AWS services from within the container if needed)
    awscli \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# --- Node.js Installation ---
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
RUN node -v && npm -v

# --- ROS2 Workspace and Application Setup ---
ENV APP_ROOT=/opt/ros2_saas_app
ENV ROS_WORKSPACE=${APP_ROOT}/colcon_ws
RUN mkdir -p ${ROS_WORKSPACE}/src
RUN mkdir -p ${APP_ROOT}/frontend # For frontend static files
RUN mkdir -p ${APP_ROOT}/backend  # For Node.js backend code
# RUN mkdir -p /var/log/supervisor # If using supervisor

WORKDIR ${APP_ROOT}

# --- Application Code ---
# Code will be copied during the image build process by GitHub Actions or a manual build.
# This Dockerfile defines the environment where the code will run.

# Example: Copying a pre-built ROS workspace (install directory)
# ARG ROS_WORKSPACE_INSTALL_DIR=colcon_ws_built/install
# COPY ${ROS_WORKSPACE_INSTALL_DIR} ${ROS_WORKSPACE}/install/

# Example: Copying Node.js backend source and installing dependencies
# COPY ./backend_src/package.json ./backend_src/package-lock.json* ${APP_ROOT}/backend/
# RUN cd ${APP_ROOT}/backend && npm install --production
# COPY ./backend_src/ ${APP_ROOT}/backend/

# Example: Copying frontend static files
# COPY ./frontend_dist/ ${APP_ROOT}/frontend/

# For this generic Dockerfile, we assume the GitHub Actions workflow (`aws_ecr_push.yml`)
# will handle checking out the code from `src_projects/` (or user provides it)
# and building the ROS workspace, then copying the necessary built artifacts,
# backend code, and frontend code into the correct locations before building this final image.
# Alternatively, this Dockerfile could be multi-stage, building ROS and Node.js apps first.

# For a simpler single Dockerfile that does everything (less optimal for layering/caching):
# 1. COPY src_projects/ros2-saas-ide-config (etc.) ${ROS_WORKSPACE}/src/ros2-saas-ide-config
# 2. RUN source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${ROS_WORKSPACE} && rosdep install ... && colcon build ...
# 3. COPY src_projects/ros2-front-end ${APP_ROOT}/frontend
# 4. COPY Node.js backend src ${APP_ROOT}/backend && cd ${APP_ROOT}/backend && npm install


# --- ROS Environment Sourcing ---
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
RUN echo "if [ -f ${ROS_WORKSPACE}/install/local_setup.bash ]; then source ${ROS_WORKSPACE}/install/local_setup.bash; fi" >> ~/.bashrc
RUN echo "export APP_ROOT=${APP_ROOT}" >> ~/.bashrc
RUN echo "export ROS_WORKSPACE=${ROS_WORKSPACE}" >> ~/.bashrc

# --- Ports ---
# Define ports that the application components will use.
# These will be mapped in ECS Task Definitions or EC2 security groups.
EXPOSE 80   # For HTTP (e.g., Nginx or Node.js frontend serving)
EXPOSE 443  # For HTTPS
EXPOSE 3000 # Default for Node.js backend
# EXPOSE 11311 # ROS1 Master (legacy)
EXPOSE 9090 # rosbridge_server (if used)
# Gazebo typically communicates over port 11345, but this is often within the container/host network.

# --- Entrypoint/CMD ---
# This script will set up the environment and start the main application process(es).
# It might launch ROS nodes, the Node.js backend, and Nginx (if used).
COPY entrypoint_aws.sh /entrypoint_aws.sh
RUN chmod +x /entrypoint_aws.sh

ENTRYPOINT ["/entrypoint_aws.sh"]
# The CMD can be used to pass default arguments to the entrypoint or a default command.
# For ECS, the command in the Task Definition often overrides this.
# Example: CMD ["run_all_services"] (if entrypoint_aws.sh interprets this)
CMD ["bash"] # Default to bash for interactive use or if entrypoint handles startup

# --- Build Instructions (Informational, for local testing) ---
# To build this Docker image locally (assuming code is structured correctly):
# 1. Place `entrypoint_aws.sh` in the same directory.
# 2. (If building ROS workspace in Dockerfile) Ensure `src_projects` are available in build context.
#    docker build --build-arg ROS_WORKSPACE_SRC_DIR=./src_projects -t ros2-saas-aws .
# 3. (If copying pre-built artifacts)
#    docker build \
#      --build-arg ROS_WORKSPACE_INSTALL_DIR=./path_to_ros_install \
#      --build-arg NODE_BACKEND_DIR=./path_to_node_backend \
#      --build-arg FRONTEND_DIR=./path_to_frontend_dist \
#      -t ros2-saas-aws .

# The GitHub Actions workflow `aws_ecr_push.yml` will automate the build
# and pushing to ECR, likely involving multiple stages or careful context management.
```

This `Dockerfile`:
-   Is based on `ros:jazzy-desktop-full`.
-   Installs essential system packages, Node.js, and AWS CLI.
-   Sets up common environment variables and directories (`APP_ROOT`, `ROS_WORKSPACE`).
-   Includes comments on how application code (ROS workspace, Node.js backend, frontend) would typically be integrated during the build process (often managed by a CI/CD pipeline like the one defined in `aws_ecr_push.yml`).
-   Sources ROS environment scripts in `.bashrc`.
-   Exposes typical ports.
-   Uses an `entrypoint_aws.sh` script (to be created next) for container initialization and service startup.
-   Defaults to `bash` as the `CMD`, suitable for development or if the entrypoint fully manages the application lifecycle. For ECS, the task definition's command will often be the effective one.

Next, I will create the `entrypoint_aws.sh` script.
