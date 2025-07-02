# Dockerfile for Google Cloud Platform (GCP) Deployment (ROS2 Jazzy, Gazebo, Node.js)
# This image can be pushed to Google Container Registry (GCR) or Artifact Registry
# and used by Google Kubernetes Engine (GKE) or Cloud Run.

# --- Base Image: ROS2 Jazzy with Gazebo ---
# Using an image that includes ROS desktop and Gazebo tools.
# For GPU workloads on GKE, ensure node pools have GPUs and appropriate drivers.
FROM ros:jazzy-desktop-full

LABEL maintainer="Your Name <user@todo.todo>"
LABEL description="ROS2 Jazzy with Gazebo, Node.js for GCP (GKE/Cloud Run) deployment."

ENV ROS_DISTRO=jazzy
ENV DEBIAN_FRONTEND=noninteractive

# For GPU acceleration with NVIDIA on GKE (ensure GKE node pool has NVIDIA drivers)
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
    # Nginx (optional, if serving frontend directly from this container, or use GCLB/Istio)
    # nginx \
    # Supervisor (optional, for process management if not using Kubernetes pod structure effectively)
    # supervisor \
    terminator \
    mesa-utils \
    # Google Cloud SDK (gcloud CLI - useful for interacting with GCP services if needed from container)
    # This can make the image larger. Install only if necessary.
    # apt-transport-https \
    # ca-certificates \
    # gnupg \
    # && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    # && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    # && apt-get update && apt-get install -y google-cloud-sdk \
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
# Code will be copied during the image build process by Cloud Build or a manual build.
# This Dockerfile defines the environment where the code will run.
# Similar to the AWS ECR Dockerfile, this assumes Cloud Build will handle
# checking out code from `src_projects/` and building/copying artifacts.

# Example COPY commands (these would be part of a Cloud Build step or multi-stage Dockerfile):
# COPY ../ros2-front-end ${APP_ROOT}/frontend/
# COPY ../backend_nodejs_app ${APP_ROOT}/backend/
# RUN cd ${APP_ROOT}/backend && npm install --production
#
# COPY ../ros_ws_source/src ${ROS_WORKSPACE}/src/
# RUN . /opt/ros/${ROS_DISTRO}/setup.sh && cd ${ROS_WORKSPACE} && rosdep install -i --from-path src -y -r
# RUN . /opt/ros/${ROS_DISTRO}/setup.sh && cd ${ROS_WORKSPACE} && colcon build --symlink-install
#
# For a final image, you'd typically copy only the built artifacts:
# COPY --from=builder ${ROS_WORKSPACE}/install ${ROS_WORKSPACE}/install
# COPY --from=builder ${APP_ROOT}/backend ${APP_ROOT}/backend
# COPY --from=builder ${APP_ROOT}/frontend ${APP_ROOT}/frontend


# --- ROS Environment Sourcing ---
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
RUN echo "if [ -f ${ROS_WORKSPACE}/install/local_setup.bash ]; then source ${ROS_WORKSPACE}/install/local_setup.bash; fi" >> ~/.bashrc
RUN echo "export APP_ROOT=${APP_ROOT}" >> ~/.bashrc
RUN echo "export ROS_WORKSPACE=${ROS_WORKSPACE}" >> ~/.bashrc

# --- Ports ---
# Define ports that the application components will use.
# These will be mapped in Kubernetes Service definitions or Cloud Run service settings.
EXPOSE 8080 # Common port for applications on GKE/Cloud Run, often mapped from 80/443 by load balancer
            # If your app (Node.js or Nginx inside) listens on 80, expose 80.
            # If it listens on 3000 (Node.js), expose 3000.
            # K8s service will map this.
# EXPOSE 80   # If Nginx or app listens on 80 directly
# EXPOSE 3000 # If Node.js backend listens on 3000 directly
# EXPOSE 9090 # rosbridge_server (if used)

# --- Entrypoint/CMD ---
# This script will set up the environment and start the main application process(es).
# For Kubernetes, the CMD and args in the manifest often override Dockerfile's CMD.
COPY entrypoint_gcp.sh /entrypoint_gcp.sh
RUN chmod +x /entrypoint_gcp.sh

ENTRYPOINT ["/entrypoint_gcp.sh"]
# Default CMD. Can be overridden by Kubernetes pod spec `command` and `args`.
# Example: CMD ["run_web_server"] (if entrypoint_gcp.sh interprets this)
CMD ["bash"] # Default to bash for interactive use or if entrypoint handles startup

# --- Build Instructions (Informational, for local testing) ---
# To build this Docker image locally (assuming code is structured correctly):
# 1. Place `entrypoint_gcp.sh` in the same directory.
# 2. Ensure source code (Phases 1-6) is available in the build context as expected by COPY commands.
#    (e.g., if Dockerfile copies from `../ros2-front-end`, context should be parent dir)
#    docker build -t ros2-saas-gcp .
#
# Cloud Build (`cloudbuild.yaml`) will automate this process in GCP.
```

This `Dockerfile` for GCP is very similar to the AWS one:
-   Based on `ros:jazzy-desktop-full`.
-   Installs Node.js and essential tools. (Commented out Google Cloud SDK installation for smaller image, can be added if needed).
-   Sets up environment variables and directories.
-   Includes comments on how application code would be integrated, typically by a Cloud Build process copying from a monorepo structure.
-   Sources ROS environment scripts.
-   Exposes port `8080` as a common practice for GKE/Cloud Run, but this should be adjusted to what the application inside the container actually listens on (e.g., port 80 for Nginx, port 3000 for a Node.js app). Kubernetes services will handle mapping.
-   Uses an `entrypoint_gcp.sh` script (to be created next).
-   Defaults to `bash` for `CMD`.

Next, I will create the `entrypoint_gcp.sh` script.
