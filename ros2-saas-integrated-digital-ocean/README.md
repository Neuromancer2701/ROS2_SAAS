# ROS2 SaaS Platform - DigitalOcean Integrated Deployment

This repository provides the necessary configurations and scripts to deploy the ROS2 SaaS application platform on a DigitalOcean Droplet. It leverages Docker to containerize the ROS2 environment (with Gazebo and Node.js) and Nginx to serve the frontend and proxy API requests.

## Deployment Strategy

1.  **Droplet Provisioning:** A bash script (`setup_droplet.sh`) automates the setup of an Ubuntu 24.04 LTS DigitalOcean droplet. This includes installing Docker, Nginx, Node.js, PostgreSQL, and ROS2 Jazzy.
2.  **Source Code Management:**
    *   This repository (`ros2-saas-integrated-digital-ocean`) contains the Dockerfile, Nginx configuration, entrypoint script, and the droplet setup script.
    *   **Crucially, you will need to manually clone or copy the source code from your original ROS2 SaaS project phases (Phases 1-6, e.g., `ros2-saas-ide-config`, `ros2-package-generator`, `ros2-front-end`, etc.) into a specific directory on the provisioned DigitalOcean droplet.** The `setup_droplet.sh` script will create a placeholder directory (e.g., `/srv/ros2_saas_app/src_projects_to_mount`) for this purpose.
3.  **Dockerization:** A `Dockerfile` is provided to build an image containing:
    *   ROS2 Jazzy (desktop-full, including Gazebo and RViz).
    *   Node.js (for the backend API).
    *   Nginx (configured by `nginx.conf`).
    *   An `entrypoint_do.sh` script to initialize the container environment.
4.  **Application Execution:**
    *   The `setup_droplet.sh` script will build the Docker image and run a container from it.
    *   The Docker container will:
        *   Run Nginx to serve the React frontend (from the mounted `ros2-front-end` project).
        *   Run a Node.js backend (code for this backend should be part of your mounted projects or built into the image if you customize the Dockerfile). This backend will handle API requests and can interact with ROS tools or scripts.
        *   Provide an environment where ROS2 nodes and Gazebo simulations *can* be launched (e.g., via the Node.js backend calling ROS commands, or by `docker exec`-ing into the container).
5.  **Database:** PostgreSQL is installed directly on the droplet and configured by `setup_droplet.sh`. The application within Docker can connect to this database on the host.

## Included Files in This Phase

-   **`Dockerfile`**: Builds the main application image with ROS2, Gazebo, Node.js, and Nginx.
-   **`nginx.conf`**: Nginx configuration to serve the React frontend and proxy API calls to the Node.js backend.
-   **`entrypoint_do.sh`**: Entrypoint script for the Docker container to set up the environment and start services.
-   **`setup_droplet.sh`**: Bash script to automate the provisioning of a DigitalOcean droplet.
-   **`README.md`**: This file.

## Deployment Instructions

### Prerequisites

1.  A DigitalOcean Account.
2.  `doctl` (DigitalOcean Command Line Tool) installed and configured locally (optional, for programmatic droplet creation, otherwise use the Web UI).
3.  An SSH key pair added to your DigitalOcean account.
4.  This repository (`ros2-saas-integrated-digital-ocean`) cloned to your local machine.
5.  Your ROS2 SaaS project source code (from Phases 1-6) available locally, ready to be transferred to the droplet.

### Steps

1.  **Provision a DigitalOcean Droplet:**
    *   **Recommended Specs:** Ubuntu 24.04 LTS. For running Gazebo and multiple ROS nodes, choose a droplet with sufficient CPU and RAM (e.g., a General Purpose Droplet with at least 4GB RAM / 2 vCPUs, or a CPU-Optimized Droplet. If GPU acceleration for Gazebo is desired, consider GPU-Optimized Droplets, though this adds complexity).
    *   Ensure your SSH key is selected during droplet creation.
    *   You can create the droplet via the DigitalOcean Web UI or `doctl`.

2.  **SSH into the Droplet:**
    Once the droplet is created, SSH into it as `root`:
    ```bash
    ssh root@<your_droplet_ip>
    ```

3.  **Clone This Repository onto the Droplet:**
    Inside the droplet:
    ```bash
    git clone https://github.com/your-username/ros2-saas-projects.git # Or your specific fork/repo name
    cd ros2-saas-projects/ros2-saas-integrated-digital-ocean
    ```
    *(Adjust the clone URL and path as necessary if you've structured your projects differently)*

4.  **Make `setup_droplet.sh` Executable:**
    ```bash
    chmod +x setup_droplet.sh
    ```

5.  **Run the Setup Script:**
    Execute the script. You can optionally pass your main application's Git repository URL if it's different from a default (though the script currently assumes it's being run from within the cloned `ros2-saas-integrated-digital-ocean` directory).
    ```bash
    sudo ./setup_droplet.sh # GIT_REPO_URL is primarily for future use if script cloned things itself
    ```
    The script will:
    *   Install Docker, Nginx, Node.js, PostgreSQL, and ROS2.
    *   Configure PostgreSQL with a database and user (credentials will be saved in `/root/db_credentials.txt` on the droplet - **secure this file!**).
    *   Configure Nginx using `nginx.conf`.
    *   Create necessary application directories (e.g., `/srv/ros2_saas_app`).
    *   Build the Docker image specified in `Dockerfile`.
    *   Run the Docker container.
    *   Set up UFW firewall rules.

6.  **Populate `src_projects_to_mount`:**
    *   After `setup_droplet.sh` completes, it will have created a directory like `/srv/ros2_saas_app/src_projects_to_mount`.
    *   You **must** now transfer your ROS2 SaaS project directories (from Phases 1-6: `ros2-saas-ide-config`, `ros2-package-generator`, `ros2-gazebo-integration`, `ros2-debug-tools`, `ros2-cicd-pipeline`, `ros2-front-end`) from your local machine (or another Git source) into this `/srv/ros2_saas_app/src_projects_to_mount` directory on the droplet.
    *   **Example using `scp` (run from your local machine):**
        ```bash
        # Assuming your Phase 1-6 projects are in a local directory called 'my_ros_saas_phases_code'
        scp -r /path/to/your/local/my_ros_saas_phases_code/* root@<your_droplet_ip>:/srv/ros2_saas_app/src_projects_to_mount/
        ```
        Ensure the structure inside `/srv/ros2_saas_app/src_projects_to_mount/` matches what the application expects (e.g., `/srv/ros2_saas_app/src_projects_to_mount/ros2-front-end/index.html`).
    *   The Docker container (started by `setup_droplet.sh`) mounts `/srv/ros2_saas_app/src_projects_to_mount` to `/opt/ros2_saas_app/colcon_ws/src_projects_mounted` inside the container.
    *   The frontend is specifically mounted from `/srv/ros2_saas_app/src_projects_to_mount/ros2-front-end` to `/opt/ros2_saas_app/frontend` for Nginx.

7.  **Restart Docker Container (If necessary after copying files):**
    If you copied the `src_projects` *after* the `setup_droplet.sh` script started the container, you might need to restart the container for it to pick up the newly mounted files correctly, especially if the entrypoint script or services within it depend on these files at startup.
    ```bash
    # On the droplet
    docker restart ros2-saas-app
    ```

8.  **Access Your Application:**
    Open your web browser and navigate to `http://<your_droplet_ip>`. You should see the React frontend. API calls will be proxied to the Node.js backend running within Docker.

### Interacting with the Application

-   **Frontend:** Accessible via `http://<your_droplet_ip>`.
-   **API Backend:** Endpoints like `http://<your_droplet_ip>/api/...` are proxied by Nginx to the Node.js backend.
-   **ROS & Gazebo:**
    *   To interact with ROS or launch simulations, you'll typically `docker exec` into the running container:
        ```bash
        # On the droplet
        docker exec -it ros2-saas-app bash
        ```
    *   Inside the container, the ROS environment will be sourced. You can then use `ros2` commands, launch Gazebo, etc.
        ```bash
        # Inside the container
        source /opt/ros2_saas_app/colcon_ws/install/local_setup.bash # If you build a workspace inside
        ros2 launch my_package my_simulation.launch.py
        # or
        gazebo /opt/ros2_saas_app/colcon_ws/src_projects_mounted/ros2-gazebo-integration/tb3_simulation_pkg/worlds/dummy.world
        ```
    *   **GUI Applications (Gazebo Client, RViz):** Running GUI applications from a Docker container on a remote server requires X11 forwarding or a VNC setup. This is an advanced topic not covered by the basic setup. For development, running these tools locally and connecting to ROS topics/services from the droplet might be easier if the network is configured (e.g. using a ROS VPN or specific DDS settings).

### Managing Services

-   **Docker Container:**
    ```bash
    docker ps # List running containers
    docker logs -f ros2-saas-app # View container logs
    docker stop ros2-saas-app
    docker start ros2-saas-app
    docker restart ros2-saas-app
    ```
-   **Nginx (on the droplet):**
    ```bash
    sudo systemctl status nginx
    sudo systemctl restart nginx
    sudo journalctl -u nginx -f # View Nginx logs
    ```
-   **PostgreSQL (on the droplet):**
    ```bash
    sudo systemctl status postgresql
    sudo systemctl restart postgresql
    ```

### Security Considerations

-   **Firewall:** `setup_droplet.sh` enables UFW. Review and tighten rules as necessary (`sudo ufw status`).
-   **SSH Access:** Use SSH keys, disable password authentication for SSH. Consider using `fail2ban`.
-   **Database Security:** Change the default PostgreSQL user password. Configure `pg_hba.conf` for secure access. Do not expose PostgreSQL to the public internet unless necessary and secured.
-   **Application Secrets:** Manage any API keys or sensitive configuration for your Node.js app or Python scripts using environment variables or a proper secrets management solution (not covered by this basic setup).
-   **Regular Updates:** Keep the droplet's OS and packages updated (`sudo apt update && sudo apt upgrade`).

This setup provides a comprehensive environment on DigitalOcean for running the full ROS2 SaaS application, including the frontend, backend, and the ROS/Gazebo environment within Docker. Remember to adapt paths and configurations based on your exact project structure.
```
