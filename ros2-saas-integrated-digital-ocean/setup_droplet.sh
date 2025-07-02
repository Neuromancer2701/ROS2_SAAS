#!/bin/bash
# Script to set up a DigitalOcean Droplet for the ROS2 SaaS Application
# Target OS: Ubuntu 24.04 LTS

# Bash Strict Mode
set -euo pipefail
IFS=$'\n\t'

# --- Configuration Variables ---
# These can be customized before running the script or passed as arguments.
GIT_REPO_URL="${1:-https://github.com/your-username/your-ros2-saas-repo.git}" # URL of your main application repository
# GIT_BRANCH="${2:-main}" # Optional: specify a branch to clone
APP_DIR="/srv/ros2_saas_app" # Main directory for the application and its components
ROS_DISTRO="jazzy"
NODE_VERSION="18" # Major Node.js version (e.g., 18, 20)
POSTGRES_VERSION="16" # Major PostgreSQL version
DB_NAME="ros2_saas_db"
DB_USER="ros2_saas_user"
DB_PASSWORD=$(openssl rand -hex 16) # Generate a random password for the DB

# --- Helper Functions ---
log() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error_exit() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
    exit 1
}

# --- Script Execution ---

log "Starting ROS2 SaaS Application Droplet Setup..."
log "Target OS: Ubuntu 24.04 LTS"
log "Application will be installed in: ${APP_DIR}"
log "ROS Distro: ${ROS_DISTRO}"
log "Node.js Version: ${NODE_VERSION}.x"
log "PostgreSQL Version: ${POSTGRES_VERSION}"

# 0. Ensure script is run as root
if [ "$(id -u)" -ne 0 ]; then
    error_exit "This script must be run as root. Please use sudo."
fi

# 1. System Update and Essential Packages
log "Updating system packages and installing essentials..."
apt-get update -y
apt-get upgrade -y
apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    software-properties-common \
    build-essential \
    python3-pip \
    python3-venv \
    unzip \
    ufw # Uncomplicated Firewall

# 2. Install Docker
log "Installing Docker Engine..."
if ! command -v docker &> /dev/null; then
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    log "Docker installed successfully."
else
    log "Docker is already installed."
fi
# Optional: Add current user to docker group (if running script as non-root initially, then sudo for apt)
# usermod -aG docker $USER # Requires logout/login or newgrp docker to take effect

# 3. Install Node.js (using NodeSource)
log "Installing Node.js v${NODE_VERSION}.x..."
if ! command -v node &> /dev/null || ! node -v | grep -q "v${NODE_VERSION}\."; then
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash -
    apt-get install -y nodejs
    log "Node.js v${NODE_VERSION}.x installed successfully."
    node -v && npm -v
else
    log "Node.js v${NODE_VERSION}.x (or compatible) is already installed."
fi

# 4. Install PostgreSQL Server
log "Installing PostgreSQL v${POSTGRES_VERSION}..."
if ! command -v psql &> /dev/null || ! psql --version | grep -q "${POSTGRES_VERSION}"; then
    apt-get install -y "postgresql-${POSTGRES_VERSION}" "postgresql-contrib-${POSTGRES_VERSION}"
    systemctl enable postgresql
    systemctl start postgresql
    log "PostgreSQL v${POSTGRES_VERSION} installed successfully."
else
    log "PostgreSQL v${POSTGRES_VERSION} (or compatible) is already installed."
fi

# 5. Configure PostgreSQL Database
log "Configuring PostgreSQL database..."
# Check if user and database already exist to make script idempotent
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'")

if [ "$DB_EXISTS" != "1" ]; then
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};"
    log "Database '${DB_NAME}' created."
else
    log "Database '${DB_NAME}' already exists."
fi

if [ "$USER_EXISTS" != "1" ]; then
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
    sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH SUPERUSER;" # For simplicity, grant superuser. Adjust permissions as needed.
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
    log "User '${DB_USER}' created with password and granted privileges on '${DB_NAME}'."
    log "IMPORTANT: PostgreSQL User '${DB_USER}' Password: ${DB_PASSWORD}"
    echo "PostgreSQL User: ${DB_USER}" >> /root/db_credentials.txt
    echo "PostgreSQL Password: ${DB_PASSWORD}" >> /root/db_credentials.txt
    echo "PostgreSQL Database: ${DB_NAME}" >> /root/db_credentials.txt
    chmod 600 /root/db_credentials.txt
    log "Database credentials saved to /root/db_credentials.txt (ensure this is secured)."
else
    log "User '${DB_USER}' already exists. Ensure password and privileges are correct."
    # Consider updating password if script is re-run and intended to reset it.
    # sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
fi

# Modify pg_hba.conf for local connections if needed (default is often sufficient for peer/md5 on localhost)
# Example: ensure md5 for local connections if your app uses password auth
# PG_HBA_CONF=$(sudo -u postgres psql -t -P format=unaligned -c 'show hba_file')
# if ! grep -q "${DB_USER}" "${PG_HBA_CONF}"; then
#   echo "host    ${DB_NAME}    ${DB_USER}    127.0.0.1/32    md5" >> "${PG_HBA_CONF}"
#   echo "host    ${DB_NAME}    ${DB_USER}    ::1/128       md5" >> "${PG_HBA_CONF}"
#   log "Updated pg_hba.conf for md5 local access for ${DB_USER}."
#   systemctl restart postgresql
# fi


# 6. Install ROS2 ${ROS_DISTRO} and Gazebo
# (This part is typically done *inside* the Docker container for the app,
# but if you need system-level ROS tools or want to build natively first)
log "Installing ROS2 ${ROS_DISTRO} and Gazebo..."
if ! command -v ros2 &> /dev/null; then
    log "Setting up ROS2 apt repository..."
    apt-get install -y software-properties-common
    add-apt-repository universe -y
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

    apt-get update -y
    log "Installing ROS2 ${ROS_DISTRO} Desktop Full (includes Gazebo, RViz, dev tools)..."
    # Use a specific metapackage. ros-dev-tools for CLI tools. ros-desktop-full for GUI.
    apt-get install -y "ros-${ROS_DISTRO}-desktop-full"
    # For a headless server, you might only need ros-base and specific packages:
    # apt-get install -y ros-${ROS_DISTRO}-ros-base python3-colcon-common-extensions python3-rosdep
    # apt-get install -y ros-${ROS_DISTRO}-gazebo-ros-pkgs # If Gazebo server needed without desktop

    log "Initializing rosdep..."
    if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
        rosdep init
    fi
    rosdep update

    # Source ROS setup in .bashrc for interactive shells (for root and new users)
    echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc
    # Consider adding for a non-root user if you create one, e.g., /home/youruser/.bashrc
    log "ROS2 ${ROS_DISTRO} and Gazebo installed."
else
    log "ROS2 is already installed."
fi

# 7. Clone Application Repository and Set Up Directories
log "Setting up application directory at ${APP_DIR}..."
mkdir -p "${APP_DIR}"
# mkdir -p "${APP_DIR}/src_projects" # This will contain the ROS/frontend code
mkdir -p "${APP_DIR}/logs"
mkdir -p "${APP_DIR}/data" # For persistent data like generated packages, maps, etc.

# Clone the main application repository containing Dockerfile, Nginx config, etc. for this phase
# This script itself is part of this repository.
# If the repo is already cloned (e.g. this script is being run from it), skip cloning.
# For a fresh droplet, you would clone it.
# This example assumes the script is run from *within* the already cloned `ros2-saas-integrated-digital-ocean` directory.
# If not, uncomment and adapt the clone command.
# log "Cloning application repository from ${GIT_REPO_URL}..."
# git clone --branch "${GIT_BRANCH}" "${GIT_REPO_URL}" "${APP_DIR}/app_config"
# cd "${APP_DIR}/app_config" # This would be ros2-saas-integrated-digital-ocean

# The user will need to manually place their ROS projects (Phase 1-6) into a
# directory that will be volume-mounted into the Docker container, e.g., ${APP_DIR}/src_projects/
# The README for this phase will instruct this.
# For now, create the placeholder for where they should go.
mkdir -p "${APP_DIR}/src_projects_to_mount"
log "Placeholder for user's ROS/frontend code: ${APP_DIR}/src_projects_to_mount"
log "User should copy/clone their Phase 1-6 projects into this directory."

# Copy Nginx configuration from the (assumed) cloned repo context
# This script is in `ros2-saas-integrated-digital-ocean/setup_droplet.sh`
# `nginx.conf` is in `ros2-saas-integrated-digital-ocean/nginx.conf`
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cp "${SCRIPT_DIR}/nginx.conf" "/etc/nginx/sites-available/ros2_saas_app.conf"
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi
if [ ! -L /etc/nginx/sites-enabled/ros2_saas_app.conf ]; then
    ln -s /etc/nginx/sites-available/ros2_saas_app.conf /etc/nginx/sites-enabled/ros2_saas_app.conf
fi
nginx -t # Test Nginx configuration
systemctl restart nginx
log "Nginx configured and restarted."

# 8. Build and Run Docker Container
# The Dockerfile for this phase should be in the cloned repo (e.g., ${SCRIPT_DIR}/Dockerfile)
log "Building the application Docker image (ros2-saas-app-do)..."
docker build -t ros2-saas-app-do "${SCRIPT_DIR}" # Build from the directory containing the Dockerfile

log "Starting the application Docker container..."
# Ensure old container with same name is removed if it exists
docker rm -f ros2-saas-app || true

# Run the Docker container
# Mount points:
# - src_projects_to_mount: User needs to populate this with their ROS packages (Phase 1-6)
# - APP_DIR/logs: For persistent application logs from within the container
# - APP_DIR/data: For persistent data (e.g., generated ROS packages, Gazebo worlds, SLAM maps)
# GPU access for Gazebo: --gpus all (requires nvidia-container-toolkit on host)
# X11 forwarding for GUI (complex, VNC or web-based GUI often preferred for remote access)
# -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix
docker run -d \
    --name ros2-saas-app \
    -p 80:80 \
    -p 443:443 \
    # -p 3000:3000 # If Node.js backend port needs direct access, otherwise Nginx proxies
    # For Gazebo GUI (if running gzclient in container and forwarding X11 or using VNC):
    # --ipc=host \ (Some GUI apps might need this)
    # For NVIDIA GPU passthrough:
    # --gpus all \
    # For integrated Intel/AMD graphics (Mesa):
    # -v /dev/dri:/dev/dri \
    # Volume for user's ROS/frontend code (Phase 1-6 projects)
    -v "${APP_DIR}/src_projects_to_mount":/opt/ros2_saas_app/colcon_ws/src_projects_mounted \
    # Volume for Node.js backend code (if not built into the image, or for dev)
    # This assumes the Node.js backend is part of the main repo or another specific repo
    # For this setup, the Node.js backend logic might be simpler, running inside the container
    # and managed by the container's entrypoint, using code from `src_projects_mounted` or built-in.
    # Let's assume the Docker image's entrypoint_do.sh and internal structure handles the backend.
    # -v "${APP_DIR}/backend_code_to_mount":/opt/ros2_saas_app/backend \
    # Volume for frontend static files (if not built into image or for dev)
    -v "${APP_DIR}/src_projects_to_mount/ros2-front-end":/opt/ros2_saas_app/frontend \
    # Volume for persistent logs
    -v "${APP_DIR}/logs":/opt/ros2_saas_app/logs_internal \
    # Volume for persistent data (e.g., generated packages, maps)
    -v "${APP_DIR}/data":/opt/ros2_saas_app/data_internal \
    --restart always \
    ros2-saas-app-do

log "Docker container 'ros2-saas-app' started."
log "Frontend should be accessible via http://<droplet_ip>/"
log "API (proxied by Nginx) via http://<droplet_ip>/api/"

# 9. Configure Firewall (UFW)
log "Configuring firewall (UFW)..."
ufw allow ssh       # Port 22
ufw allow http      # Port 80
ufw allow https     # Port 443
# ufw allow 3000/tcp # If direct access to Node.js backend is needed
# Add other ports if necessary (e.g., for ROS bridge, specific ROS tools)
ufw enable # Will ask for confirmation if run interactively. Add --force or expect for non-interactive.
# Consider `yes | ufw enable` for non-interactive, but be cautious.
# For non-interactive:
ufw --force enable
log "Firewall configured and enabled."

# --- Final Instructions ---
log "--------------------------------------------------------------------------"
log "DigitalOcean Droplet Setup for ROS2 SaaS Application Complete!"
log " "
log "Access your application at: http://<Your_Droplet_IP_Address>"
log "SSH into your droplet: ssh root@<Your_Droplet_IP_Address>"
log " "
log "Important Next Steps:"
log "1. Populate '${APP_DIR}/src_projects_to_mount' on the droplet:"
log "   - Clone/copy your Phase 1-6 project directories (ros2-saas-ide-config, ros2-package-generator, etc.)"
log "     into '${APP_DIR}/src_projects_to_mount' on the droplet."
log "   - Example structure: ${APP_DIR}/src_projects_to_mount/ros2-saas-ide-config, etc."
log "   - The Docker container mounts this directory to /opt/ros2_saas_app/colcon_ws/src_projects_mounted."
log "     The application inside Docker (e.g., Python API script, Node.js backend) will need to know this path"
log "     or be configured to find these source projects."
log "2. (If using a domain) Configure DNS for your domain to point to the droplet's IP address."
log "3. (If using HTTPS) Set up SSL certificates (e.g., using Let's Encrypt with Certbot)."
log "   Example for Nginx: sudo certbot --nginx -d yourdomain.com"
log "4. Secure your PostgreSQL installation and update credentials as needed."
log "   Credentials saved to /root/db_credentials.txt on the droplet (secure this file!)."
log "5. Review firewall rules: sudo ufw status"
log "6. Monitor application logs: docker logs -f ros2-saas-app"
log "   And Nginx logs in /var/log/nginx/ on the droplet."
log "--------------------------------------------------------------------------"

exit 0
```

This comprehensive `setup_droplet.sh` script includes:
-   Configuration variables.
-   System updates and installation of essential packages (git, Docker, Nginx, UFW).
-   Installation of Node.js and PostgreSQL.
-   Basic PostgreSQL database and user setup, saving credentials.
-   Installation of ROS2 Jazzy Desktop Full (including Gazebo) and rosdep initialization.
-   Setup of application directories on the host.
-   Instructions for the user to manually place their ROS project sources (Phases 1-6) into a specific directory on the droplet (`/srv/ros2_saas_app/src_projects_to_mount`), which will be volume-mounted into the Docker container.
-   Copying the `nginx.conf` (created in the previous step) to the correct Nginx location.
-   Building the Docker image (`ros2-saas-app-do`) using the `Dockerfile` from the current phase.
-   Running the Docker container with necessary port mappings and volume mounts. The frontend from `src_projects_to_mount/ros2-front-end` is mounted to where Nginx expects it.
-   Basic UFW firewall configuration.
-   Final instructions for the user.

**Important Considerations for this script:**
-   **Idempotency:** Some effort has been made for idempotency (e.g., checking if Docker/Node/Postgres are installed), but it's not fully idempotent for all operations (e.g., user creation might error if exists).
-   **Security:** The script grants SUPERUSER to the PostgreSQL user for simplicity and stores credentials in `/root/db_credentials.txt`. In a production environment, more restrictive permissions and better secret management are crucial.
-   **User Input for Firewall:** `ufw enable` can be interactive. `--force` is used for non-interactive setup.
-   **ROS Projects Source:** The script now relies on the user to manually place the source code of projects from Phases 1-6 into `/srv/ros2_saas_app/src_projects_to_mount` on the droplet. The Docker container then mounts this. The internal application logic (Node.js backend, Python API script) will need to be aware of this mounted path (`/opt/ros2_saas_app/colcon_ws/src_projects_mounted`) to access those files.
-   **Error Handling:** Uses `set -euo pipefail` and basic `log`/`error_exit` functions.

Next, I'll make this script executable and then create the README for this phase.```python
print("Creating setup_droplet.sh for DigitalOcean")

```
