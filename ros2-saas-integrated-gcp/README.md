# ROS2 SaaS Platform - Google Cloud Platform (GCP) Integrated Deployment

This document outlines the strategy and provides templates for deploying the ROS2 SaaS application platform on Google Cloud Platform (GCP), primarily using Google Kubernetes Engine (GKE), Google Container Registry (GCR) or Artifact Registry, Cloud SQL for PostgreSQL, and Cloud Build for CI/CD.

## Deployment Strategy Overview

1.  **Source Code Management:**
    *   This `ros2-saas-integrated-gcp` directory will contain this README and placeholder directories for Kubernetes manifests (`k8s/`) and setup scripts (`scripts/`).
    *   You will need to manually clone or copy the source code from your original ROS2 SaaS project phases (Phases 1-6, e.g., `ros2-saas-ide-config`, `ros2-package-generator`, `ros2-front-end`, etc.) into a `src_projects/` subdirectory within this `ros2-saas-integrated-gcp` project structure. This `src_projects/` directory will be part of the Docker build context.

2.  **Dockerization:**
    *   A `Dockerfile` (content provided below) will be used to build an image containing ROS2 Jazzy (with Gazebo), Node.js, and your application code.
    *   An `entrypoint_gcp.sh` script (content provided below) will handle container initialization.

3.  **Container Registry:**
    *   The Docker image will be built and pushed to Google Container Registry (GCR) or Artifact Registry using Google Cloud Build.

4.  **CI/CD with Cloud Build:**
    *   A `cloudbuild.yaml` file (content provided below) will define the CI/CD pipeline to:
        *   Build the Docker image.
        *   Push the image to GCR/Artifact Registry.
        *   Optionally, deploy to GKE by updating Kubernetes manifests.

5.  **Database with Cloud SQL:**
    *   A Cloud SQL for PostgreSQL instance will serve as the backend database. Scripts/commands for setup are outlined below.

6.  **Application Deployment on GKE:**
    *   Kubernetes manifest files (`k8s/deployment.yaml`, `k8s/service.yaml`, etc. - content examples provided below) will define how the application runs on GKE. This includes:
        *   Deployments for your application container(s) (e.g., frontend/backend pod, ROS master/simulation pod).
        *   Services to expose your application (e.g., via LoadBalancer).
        *   PersistentVolumeClaims if stateful storage is needed for ROS bags, Gazebo worlds, etc. (potentially using Cloud Storage via a FUSE CSI driver or directly by the application).

7.  **Persistent Storage (Optional):**
    *   Google Cloud Storage buckets can be used for storing ROS bags, Gazebo models/worlds, generated packages, or other artifacts.

## Instructions to Create Files

You will need to create the following files within your `ros2-saas-integrated-gcp` project directory. The content for each is provided below.

### 1. Project Structure

Create the following directory structure:
```
ros2-saas-integrated-gcp/
├── Dockerfile
├── entrypoint_gcp.sh
├── cloudbuild.yaml
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── (other manifests like ingress.yaml, persistentvolumeclaim.yaml if needed)
├── scripts/
│   └── setup_gcp_resources.sh (or individual gcloud commands)
├── src_projects/  <-- MANUALLY POPULATE THIS with code from Phases 1-6
│   ├── ros2-saas-ide-config/
│   ├── ros2-package-generator/
│   ├── ros2-gazebo-integration/
│   ├── ros2-debug-tools/
│   ├── ros2-cicd-pipeline/ (for reference)
│   └── ros2-front-end/
└── README.md       <-- This file
```

### 2. `Dockerfile`

Create a file named `Dockerfile` in the `ros2-saas-integrated-gcp` directory with the following content:

```dockerfile
# Dockerfile for Google Cloud Platform (GCP) Deployment (ROS2 Jazzy, Gazebo, Node.js)
# This image can be pushed to Google Container Registry (GCR) or Artifact Registry
# and used by Google Kubernetes Engine (GKE) or Cloud Run.

# --- Base Image: ROS2 Jazzy with Gazebo ---
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
    terminator \
    mesa-utils \
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
RUN mkdir -p ${APP_ROOT}/frontend
RUN mkdir -p ${APP_ROOT}/backend

WORKDIR ${APP_ROOT}

# --- Application Code ---
# Cloud Build will manage the context. These COPY commands assume the build context
# is the root of `ros2-saas-integrated-gcp` and `src_projects/` is populated.

# Copy frontend (React app from ros2-front-end)
COPY src_projects/ros2-front-end ${APP_ROOT}/frontend/

# Copy and setup Node.js backend (example structure)
# Assume your Node.js backend is in src_projects/my-node-backend/
# COPY src_projects/my-node-backend ${APP_ROOT}/backend/
# RUN cd ${APP_ROOT}/backend && npm install --production
# For this example, let's assume the Node.js backend that calls Python API is simpler
# and part of the files directly in `ros2-saas-integrated-gcp` or a sub-module.
# If using the Node.js backend from Heroku phase:
COPY src_projects/ros2-saas-integrated-Heroku/backend ${APP_ROOT}/backend/
COPY src_projects/ros2-saas-integrated-Heroku/package.json ${APP_ROOT}/backend/package.json
COPY src_projects/ros2-saas-integrated-Heroku/package-lock.json ${APP_ROOT}/backend/package-lock.json
RUN cd ${APP_ROOT}/backend && npm install --production

# Copy Python API script (from Heroku phase for example)
COPY src_projects/ros2-saas-integrated-Heroku/ros_operations_api.py ${APP_ROOT}/ros_operations_api.py
# If it has requirements:
# COPY src_projects/ros2-saas-integrated-Heroku/requirements.txt ${APP_ROOT}/requirements.txt
# RUN python3 -m pip install --no-cache-dir -r ${APP_ROOT}/requirements.txt


# Copy ROS projects into the workspace src directory for building
# Adjust these paths if your src_projects structure is different.
COPY src_projects/ros2-saas-ide-config ${ROS_WORKSPACE}/src/ros2-saas-ide-config
COPY src_projects/ros2-package-generator ${ROS_WORKSPACE}/src/ros2-package-generator
COPY src_projects/ros2-gazebo-integration ${ROS_WORKSPACE}/src/ros2-gazebo-integration
COPY src_projects/ros2-debug-tools ${ROS_WORKSPACE}/src/ros2-debug-tools
# Add any other custom ROS packages from src_projects/

# Build ROS Workspace (Example - adapt to your actual packages)
# Ensure rosdep is initialized if not done in base image sufficiently
RUN rosdep init || echo "rosdep already initialized."
RUN rosdep update
RUN . /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ${ROS_WORKSPACE} && \
    rosdep install -i --from-path src -y -r --skip-keys "python-vcstool" && \
    colcon build --symlink-install --event-handlers console_direct+
    # Add specific packages to build if needed: --packages-select my_pkg1 my_pkg2

# --- ROS Environment Sourcing ---
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
RUN echo "if [ -f ${ROS_WORKSPACE}/install/local_setup.bash ]; then source ${ROS_WORKSPACE}/install/local_setup.bash; fi" >> ~/.bashrc
RUN echo "export APP_ROOT=${APP_ROOT}" >> ~/.bashrc
RUN echo "export ROS_WORKSPACE=${ROS_WORKSPACE}" >> ~/.bashrc

# --- Ports ---
# Application should listen on $PORT (usually 8080 for Cloud Run/GKE)
EXPOSE 8080

# --- Entrypoint/CMD ---
COPY entrypoint_gcp.sh /entrypoint_gcp.sh
RUN chmod +x /entrypoint_gcp.sh

ENTRYPOINT ["/entrypoint_gcp.sh"]
CMD ["bash"] # Default CMD, K8s manifest will likely override with app start command
```

### 3. `entrypoint_gcp.sh`

Create a file named `entrypoint_gcp.sh` in the `ros2-saas-integrated-gcp` directory with the following content. **Make it executable (`chmod +x entrypoint_gcp.sh`)** after creating it.

```bash
#!/bin/bash
set -e

# --- Environment Setup ---
echo "GCP (GKE/Cloud Run) Docker Entrypoint Script"
echo "Timestamp: $(date)"

ROS_DISTRO=${ROS_DISTRO:-jazzy}
APP_ROOT=${APP_ROOT:-/opt/ros2_saas_app}
ROS_WORKSPACE=${ROS_WORKSPACE:-${APP_ROOT}/colcon_ws}
PORT=${PORT:-8080} # Default port, GCP services might inject this

echo "ROS_DISTRO: ${ROS_DISTRO}"
echo "APP_ROOT: ${APP_ROOT}"
echo "ROS_WORKSPACE: ${ROS_WORKSPACE}"
echo "Application will attempt to listen on PORT: ${PORT}"

# Source ROS environment
if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  echo "Sourced ROS ${ROS_DISTRO} global setup."
fi
if [ -f "${ROS_WORKSPACE}/install/local_setup.bash" ]; then
  source "${ROS_WORKSPACE}/install/local_setup.bash"
  echo "Sourced local ROS workspace setup from ${ROS_WORKSPACE}/install."
fi

# --- Application Startup ---
# The command to run the application is typically passed via Kubernetes manifest `args` or `command`.
# This script will execute whatever is passed to it.

# Example: If the Node.js backend is the primary app component.
# Ensure server.js is configured to use `process.env.PORT || 8080`.
# The K8s manifest might specify `command: ["node", "backend/server.js"]`.
# Or, if this entrypoint is to always start the Node.js server:
# if [ -f "${APP_ROOT}/backend/server.js" ]; then
#   echo "Starting Node.js backend on port ${PORT}..."
#   cd "${APP_ROOT}/backend"
#   exec node server.js # server.js should respect PORT env var
# fi

echo "Entrypoint finished setup. Executing command from Docker CMD or K8s manifest: $@"
echo "-----------------------------------------------------------------------------"
exec "$@"
```

### 4. `cloudbuild.yaml`

Create a file named `cloudbuild.yaml` in the `ros2-saas-integrated-gcp` directory. This file defines the build steps for Google Cloud Build.

```yaml
# Google Cloud Build configuration (cloudbuild.yaml)

# Variables that can be substituted at build time
# _REGION: GCP region for Artifact Registry/GCR (e.g., us-central1)
# _IMAGE_NAME: Name of the Docker image (e.g., ros2-saas-gcp-app)
# _PROJECT_ID: Your GCP Project ID
# _GKE_CLUSTER: Name of your GKE cluster (for deploy step)
# _GKE_ZONE: Zone of your GKE cluster (for deploy step)
# _TAG_NAME: Docker image tag (e.g., latest, or commit SHA)

steps:
  # 1. Build the Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_IMAGE_NAME}/${_IMAGE_NAME}:${_TAG_NAME}' # Artifact Registry
      # Or for GCR: -t 'gcr.io/${_PROJECT_ID}/${_IMAGE_NAME}:${_TAG_NAME}'
      - '.' # Build context is the current directory (ros2-saas-integrated-gcp)
      - '-f'
      - 'Dockerfile'
    id: 'Build Docker Image'
    timeout: 3600s # Increase timeout for potentially long ROS builds

  # 2. Push the Docker image to Artifact Registry (or GCR)
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_IMAGE_NAME}/${_IMAGE_NAME}:${_TAG_NAME}'
    id: 'Push to Artifact Registry'
    waitFor: ['Build Docker Image']

  # 3. (Optional) Deploy to GKE
  # This step requires Kubernetes manifests (e.g., deployment.yaml) to be present.
  # It also requires Cloud Build service account to have GKE deploy permissions.
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk' # Provides gcloud and kubectl
    entrypoint: /bin/sh
    args:
      - '-c'
      - |
        echo "Deploying to GKE cluster: ${_GKE_CLUSTER} in zone: ${_GKE_ZONE}"
        gcloud container clusters get-credentials "${_GKE_CLUSTER}" --zone "${_GKE_ZONE}" --project "${_PROJECT_ID}"

        # Update image in Kubernetes deployment manifest(s)
        # This is a common pattern: use kustomize or sed to update the image tag.
        # Example using kubectl set image:
        echo "Updating Kubernetes deployment image..."
        kubectl set image deployment/ros2-saas-app-deployment ros2-saas-app-container=${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_IMAGE_NAME}/${_IMAGE_NAME}:${_TAG_NAME} -n default # Adjust namespace and deployment/container names
        # Or, if using kustomize:
        # cd k8s/
        # kustomize edit set image DOCKER_IMAGE_NAME=${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_IMAGE_NAME}/${_IMAGE_NAME}:${_TAG_NAME}
        # kubectl apply -k . -n default
        #
        # Or apply all manifests if they reference the image tag via a ConfigMap or similar:
        # kubectl apply -f k8s/ -n default

        echo "Deployment update initiated. Monitor status in GKE console."
    id: 'Deploy to GKE'
    waitFor: ['Push to Artifact Registry']
    # Only run deploy step if building a specific branch, e.g., main
    # if: _BRANCH_NAME == 'main'

# Specify the image to be pushed by this build
images:
  - '${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_IMAGE_NAME}/${_IMAGE_NAME}:${_TAG_NAME}'
  # Or for GCR: 'gcr.io/${_PROJECT_ID}/${_IMAGE_NAME}:${_TAG_NAME}'

# Timeout for the entire build
timeout: 7200s # 2 hours

# Options for machine type (can speed up builds)
# options:
#   machineType: 'E2_HIGHCPU_8' # Or N1_HIGHCPU_8, etc.
```
**Note on Cloud Build Variables:** Variables like `_REGION`, `_IMAGE_NAME`, `_PROJECT_ID`, `_GKE_CLUSTER`, `_GKE_ZONE`, `_TAG_NAME` are substitution variables. You can set them when triggering the build manually or define them in build triggers. `TAG_NAME` is often automatically available as a default substitution (e.g., for Git tag builds).

### 5. Kubernetes Manifests (`k8s/`)

Create a directory `k8s/`. Inside it, create `deployment.yaml` and `service.yaml`.

#### `k8s/deployment.yaml`
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ros2-saas-app-deployment
  labels:
    app: ros2-saas
spec:
  replicas: 1 # Adjust as needed
  selector:
    matchLabels:
      app: ros2-saas
      tier: frontend-backend # Or specific component
  template:
    metadata:
      labels:
        app: ros2-saas
        tier: frontend-backend
    spec:
      containers:
        - name: ros2-saas-app-container
          # IMPORTANT: Replace with your Artifact Registry or GCR image path
          # This will be updated by Cloud Build or manually.
          image: your-region-docker.pkg.dev/your-project-id/your-image-repo/your-image-name:latest
          ports:
            - containerPort: 8080 # Port your application listens on (matching Dockerfile EXPOSE and entrypoint PORT)
          # command: ["/entrypoint_gcp.sh"] # Entrypoint is already set in Dockerfile
          # args: ["specific_command_for_entrypoint"] # If entrypoint expects args
          env:
            - name: PORT
              value: "8080" # Ensure container listens on this port
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: cloudsql-db-credentials # Assumes a secret named 'cloudsql-db-credentials'
                  key: url # Key in the secret containing the full DB connection string
            - name: ROS_MASTER_URI # Example if needed, though ROS2 uses DDS
              value: "http://localhost:11311"
            - name: GAZEBO_MASTER_URI # Example
              value: "http://localhost:11345"
            # Add other environment variables
          resources:
            requests:
              memory: "1Gi" # Adjust based on needs
              cpu: "500m"   # 0.5 vCPU
            limits:
              memory: "4Gi" # Example: For ROS + Gazebo + Node.js
              cpu: "2000m"  # 2 vCPU
          # Volume mounts for persistent data (e.g., using PersistentVolumeClaim for Gazebo worlds, ROS bags)
          # volumeMounts:
          #   - name: ros-data
          #     mountPath: /opt/ros2_saas_app/data_persistent
          # For GPU nodes (if your GKE node pool has GPUs and container needs them):
          # resources:
          #   limits:
          #     nvidia.com/gpu: 1 # Request 1 GPU
      # volumes:
      #   - name: ros-data
      #     persistentVolumeClaim:
      #       claimName: ros-data-pvc # You would need to create this PVC
      # Node selector if you have specific node pools (e.g., for GPU)
      # nodeSelector:
      #   cloud.google.com/gke-accelerator: nvidia-tesla-t4
```

#### `k8s/service.yaml`
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ros2-saas-app-service
  labels:
    app: ros2-saas
spec:
  type: LoadBalancer # Exposes the service externally via a GCP Load Balancer
  # Or use ClusterIP and an Ingress controller for more advanced routing
  selector:
    app: ros2-saas
    tier: frontend-backend # Must match labels in Deployment's template.metadata.labels
  ports:
    - protocol: TCP
      port: 80 # Port the LoadBalancer listens on
      targetPort: 8080 # Port the container (ros2-saas-app-container) listens on
```
**Note on Kubernetes Manifests:**
- Replace `your-region-docker.pkg.dev/your-project-id/your-image-repo/your-image-name:latest` with the actual path to your image in Artifact Registry or GCR. Cloud Build can automate updating this.
- The `DATABASE_URL` environment variable in `deployment.yaml` assumes you have created a Kubernetes secret named `cloudsql-db-credentials` containing a key `url` with the Cloud SQL connection string. You can also inject this via other means (e.g., ConfigMaps, direct env var in CI).
- GPU configuration (`nvidia.com/gpu`) is commented out; enable it if using GPU node pools in GKE.
- Persistent storage (`PersistentVolumeClaim`) is commented out; add it if your application needs stateful storage.

### 6. Setup Scripts (`scripts/setup_gcp_resources.sh`)

Create a directory `scripts/`. Inside it, you might create a `setup_gcp_resources.sh` script or simply document the `gcloud` commands needed.

**Content for `scripts/setup_gcp_resources.sh` (Example - customize heavily):**
```bash
#!/bin/bash
set -eou pipefail

PROJECT_ID="${1:-your-gcp-project-id}" # Pass Project ID as argument
REGION="${2:-us-central1}"
ZONE="${3:-us-central1-a}"

GKE_CLUSTER_NAME="ros2-saas-cluster"
ARTIFACT_REPO_NAME="ros2-saas-images" # Docker image repository in Artifact Registry
ARTIFACT_IMAGE_NAME="ros2-saas-gcp-app"
CLOUD_SQL_INSTANCE_NAME="ros2-saas-db-instance"
DB_NAME="ros2saasdb"
DB_USER="ros2saasuser"
# DB_PASSWORD=$(openssl rand -hex 16) # Generate or set manually

echo "--- GCP Resource Setup Script (ROS2 SaaS Platform) ---"
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Zone: ${ZONE}"

gcloud config set project "${PROJECT_ID}"
gcloud config set compute/region "${REGION}"
gcloud config set compute/zone "${ZONE}"

echo "Enabling necessary GCP APIs..."
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com

# 1. Create Artifact Registry for Docker images
echo "Creating Artifact Registry repository: ${ARTIFACT_REPO_NAME}..."
gcloud artifacts repositories create "${ARTIFACT_REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker repository for ROS2 SaaS application" \
    || echo "Artifact Registry repository already exists or failed to create."

# 2. Create GKE Cluster
echo "Creating GKE cluster: ${GKE_CLUSTER_NAME}..."
# Basic cluster, adjust machine type, node count, GPU config as needed
gcloud container clusters create "${GKE_CLUSTER_NAME}" \
    --zone "${ZONE}" \
    --machine-type "e2-standard-4" # Example: 4 vCPU, 16GB RAM
    --num-nodes "1"                 # Start with 1 node, enable autoscaling if needed
    --enable-autoscaling --min-nodes 1 --max-nodes 3
    # For GPU nodes:
    # --accelerator type=nvidia-tesla-t4,count=1 \ (Ensure T4s are available in your zone)
    # --node-locations "${ZONE}" # Specify node locations
    # --workload-pool="${PROJECT_ID}.svc.id.goog" # For Workload Identity
    # After creating GPU cluster, install NVIDIA drivers:
    # kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
    || echo "GKE cluster already exists or failed to create."

# 3. Create Cloud SQL for PostgreSQL instance
echo "Creating Cloud SQL (PostgreSQL) instance: ${CLOUD_SQL_INSTANCE_NAME}..."
gcloud sql instances create "${CLOUD_SQL_INSTANCE_NAME}" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \ # Smallest tier for dev/test, choose appropriate for prod
    --region="${REGION}" \
    --root-password="your-strong-root-password" # Set a strong root password
    # --availability-type=REGIONAL # For HA
    || echo "Cloud SQL instance already exists or failed to create."

echo "Setting database user '${DB_USER}' for instance '${CLOUD_SQL_INSTANCE_NAME}'..."
# Note: Cloud SQL root password is set on instance creation.
# You'll connect as 'postgres' user with that root password to create other users/DBs,
# or gcloud can set user passwords.
# gcloud sql users create "${DB_USER}" \
#     --instance="${CLOUD_SQL_INSTANCE_NAME}" \
#     --password="${DB_PASSWORD}" \
#     || echo "DB user already exists or failed to create."
# Best practice is to create the DB and user via psql after instance is up.
# The application will connect using credentials stored in a K8s secret.

echo "Creating database '${DB_NAME}' in instance '${CLOUD_SQL_INSTANCE_NAME}'..."
gcloud sql databases create "${DB_NAME}" --instance="${CLOUD_SQL_INSTANCE_NAME}" \
    || echo "Database already exists or failed to create."

echo "--- IMPORTANT: Manual Steps Required ---"
echo "1. Set Password for DB User: Connect to '${CLOUD_SQL_INSTANCE_NAME}' as 'postgres' user (using root password set during instance creation) and run:"
echo "   CREATE USER ${DB_USER} WITH PASSWORD 'your-chosen-strong-password';"
echo "   GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
echo "2. Create Kubernetes Secret for DB Credentials: After setting the password, create a secret in GKE:"
echo "   kubectl create secret generic cloudsql-db-credentials \\"
echo "     --from-literal=username=${DB_USER} \\"
echo "     --from-literal=password='your-chosen-strong-password' \\"
echo "     --from-literal=database=${DB_NAME} \\"
echo "     --from-literal=host='<CLOUD_SQL_INSTANCE_IP_OR_PROXY_HOST>' \\" # For direct IP or Cloud SQL Proxy
echo "     --from-literal=port='5432' \\"
echo "     --from-literal=url='postgresql://${DB_USER}:your-chosen-strong-password@<CLOUD_SQL_INSTANCE_IP_OR_PROXY_HOST>:5432/${DB_NAME}'"
echo "   (Replace placeholders. For connecting from GKE, using the Cloud SQL Auth Proxy sidecar in your pod is recommended.)"

# 4. (Optional) Create Google Cloud Storage bucket
# GCS_BUCKET_NAME="ros2-saas-artifacts-${PROJECT_ID}"
# echo "Creating GCS Bucket: ${GCS_BUCKET_NAME}..."
# gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${GCS_BUCKET_NAME}/" \
#     || echo "GCS bucket already exists or failed to create."

# 5. Configure IAM Permissions for Cloud Build (if not already done)
# Cloud Build service account (PROJECT_NUMBER@cloudbuild.gserviceaccount.com) needs roles like:
# - Artifact Registry Writer (roles/artifactregistry.writer)
# - Kubernetes Engine Developer (roles/container.developer) - to deploy to GKE
# - Service Account User (roles/iam.serviceAccountUser) - if GKE uses specific SA

echo "--- Setup Script Finished ---"
echo "Remember to perform the manual steps mentioned above, especially for DB user password and K8s secret."
```
**Make this script executable (`chmod +x scripts/setup_gcp_resources.sh`)**. You'll need to replace placeholders and potentially adjust commands based on your exact needs and security practices. Using Cloud SQL Auth Proxy is recommended for connecting GKE pods to Cloud SQL.

## Deployment Workflow

1.  **Initial GCP Setup:**
    *   Ensure you have a GCP project.
    *   Install and configure `gcloud` CLI locally, or use Cloud Shell.
    *   Run parts of `scripts/setup_gcp_resources.sh` (or equivalent `gcloud` commands) to:
        *   Enable necessary APIs.
        *   Create an Artifact Registry (or GCR) repository.
        *   Create a GKE cluster.
        *   Create a Cloud SQL for PostgreSQL instance and configure the database/user.
        *   Create necessary Kubernetes secrets (e.g., for database credentials).
        *   (Optional) Create GCS buckets.

2.  **Populate `src_projects/`:**
    *   Clone or copy your Phase 1-6 project sources into the `ros2-saas-integrated-gcp/src_projects/` directory.

3.  **Configure Cloud Build Trigger (Optional):**
    *   Go to Cloud Build in the GCP Console.
    *   Create a trigger that points to your Git repository (where this `ros2-saas-integrated-gcp` project resides).
    *   Configure the trigger to use the `cloudbuild.yaml` file.
    *   Set up substitution variables for the trigger (e.g., `_REGION`, `_IMAGE_NAME`, `_GKE_CLUSTER`, `_GKE_ZONE`, `_TAG_NAME`). `_TAG_NAME` can often be dynamic like `$TAG_NAME` or `$COMMIT_SHA`.

4.  **Build and Push Docker Image:**
    *   Manually trigger a Cloud Build, or push to the branch configured in your trigger.
    *   Cloud Build will execute steps in `cloudbuild.yaml`: build the Docker image using `Dockerfile` and push it to Artifact Registry/GCR.

5.  **Deploy to GKE:**
    *   The `cloudbuild.yaml` includes an optional step to deploy to GKE. This step might involve `kubectl set image` or `kubectl apply -k` if using Kustomize.
    *   Alternatively, after the image is pushed, you can manually apply your Kubernetes manifests:
        ```bash
        gcloud container clusters get-credentials <your-gke-cluster-name> --zone <your-gke-zone> --project <your-project-id>
        # Update image tag in k8s/deployment.yaml if not done by Cloud Build
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        # Apply other manifests
        ```

6.  **Accessing the Application:**
    *   Find the external IP address of your `ros2-saas-app-service` (if type LoadBalancer):
        ```bash
        kubectl get service ros2-saas-app-service
        ```
    *   Access the application via `http://<EXTERNAL_IP>`.
    *   For HTTPS, you'd typically set up an Ingress controller with Google-managed SSL certificates or your own.

## Interacting with ROS/Gazebo on GKE

-   **`kubectl exec`:** Access a running pod:
    ```bash
    kubectl exec -it <pod-name> -c ros2-saas-app-container -- bash
    ```
    Inside the pod, you can run ROS2 commands.
-   **GUI Applications (Gazebo Client, RViz):**
    *   This is complex. Options include:
        *   X11 forwarding (difficult with Kubernetes, security concerns).
        *   VNC server running in a container, accessed via port-forwarding or Ingress.
        *   Web-based visualization tools (e.g., PlotJuggler with web UI, custom webviz).
        *   Running Gazebo server on GKE (potentially on GPU nodes) and client locally, if network/DDS is configured for remote access (e.g., VPN, Husarnet, specific DDS router settings).
-   **ROS2 Networking in GKE:** Pods can communicate with each other using Kubernetes service discovery. For external ROS2 communication, consider DDS configurations for WAN or tools like SOSS.

## Important Considerations

-   **Cost:** Monitor GCP costs for GKE, Artifact Registry, Cloud SQL, Load Balancers, etc.
-   **Security:**
    *   Use Workload Identity for GKE pods to securely access other GCP services.
    *   Manage Kubernetes secrets appropriately.
    *   Configure network policies in GKE.
    *   Secure Cloud SQL instances (e.g., use Cloud SQL Auth Proxy).
-   **GPU Nodes in GKE:** If using GPUs for Gazebo:
    *   Ensure your GKE cluster has a node pool with compatible GPUs.
    *   Install NVIDIA drivers on the nodes (GKE can automate this for some types).
    *   Request GPU resources in your Kubernetes pod spec (`nvidia.com/gpu`).
-   **Stateful Applications:** For components requiring persistent storage (e.g., ROS bags, database for Gazebo models if not using Cloud SQL directly), use PersistentVolumeClaims backed by Google Persistent Disks or Cloud Storage FUSE.

This comprehensive guide provides the templates and strategy for a GCP deployment. Remember to adapt all configurations and scripts to your specific project requirements and GCP environment.
```
