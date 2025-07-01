# ROS2 SaaS IDE Configuration

This repository contains the Dockerfile and associated scripts to set up a ROS2 Jazzy Jalisco development environment. The environment includes tools for C++ (ament_cmake) and Python (ament_python) development, Gazebo for simulation, RViz for visualization, and OpenCV for computer vision tasks.

## Prerequisites

- Docker installed on your system.

## Setup Instructions

1.  **Clone the repository (or ensure Dockerfile and `ros_entrypoint.sh` are in the same directory):**
    ```bash
    # git clone <repository-url> # If you are cloning this as a repo
    # cd ros2-saas-ide-config
    ```

2.  **Build the Docker image:**
    Open a terminal in the directory containing the `Dockerfile` and `ros_entrypoint.sh`, and run:
    ```bash
    docker build -t ros2-jazzy-dev .
    ```

3.  **Run the Docker container:**
    ```bash
    docker run -it --rm \
        -e DISPLAY=$DISPLAY \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        --name ros2_dev_container \
        ros2-jazzy-dev
    ```
    *   `-it`: Runs the container in interactive mode with a pseudo-TTY.
    *   `--rm`: Automatically removes the container when it exits.
    *   `-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix`: These lines are for GUI applications (like Gazebo and RViz) to work. You might need to adjust X11 forwarding permissions on your host machine (e.g., by running `xhost +local:docker`).
    *   `--name ros2_dev_container`: Assigns a name to the container for easier management.
    *   `ros2-jazzy-dev`: The name of the image built in the previous step.

4.  **Inside the container, you will be in the `/ros2_ws` directory.** You can use the `init_workspace.sh` script to create a sample workspace or start creating your own packages.

## Initializing a ROS2 Workspace

The Docker image includes a script `init_workspace.sh` in the `/ros2_ws` directory to help you quickly initialize a new ROS2 workspace with an example C++ package.

To use it, navigate to the `/ros2_ws` directory (which is the default working directory when you start the container) or any other location where you want to create your workspace, and run:

```bash
/ros2_ws/init_workspace.sh <workspace_name> [package_name]
# Or, if you are in /ros2_ws:
# ./init_workspace.sh <workspace_name> [package_name]
```

-   `<workspace_name>`: (Required) The name for your new workspace directory.
-   `[package_name]`: (Optional) The name for an initial C++ example package (ament_cmake). If not provided, it defaults to `my_cpp_pkg`.

Example:
```bash
# Inside the container, from /
./ros2_ws/init_workspace.sh my_new_ws my_test_pkg
cd my_new_ws
colcon build --symlink-install
source install/setup.bash
ros2 run my_test_pkg my_node
```

## Development

-   **C++ Packages:** Use `ament_cmake`.
-   **Python Packages:** Use `ament_python`.
-   **Gazebo:** Launch Gazebo using `gazebo` or through ROS launch files.
-   **RViz:** Launch RViz using `rviz2` or through ROS launch files.
-   **OpenCV:** Can be used in both C++ and Python nodes.

## Building and Sourcing

Remember to build your workspace and source the setup files:

```bash
# From the root of your workspace (e.g., /ros2_ws/my_new_ws)
colcon build --symlink-install

# Source the workspace (do this in every new terminal)
source install/setup.bash
```

To avoid sourcing in every new terminal, you can add `source /ros2_ws/install/setup.bash` (or your specific workspace path) to your `~/.bashrc` file *inside the container*. Note that the provided `ros_entrypoint.sh` already sources `/ros2_ws/install/setup.bash` if it exists, which covers the main workspace defined in the Dockerfile. For custom workspaces created with `init_workspace.sh`, you'll need to source them manually or add them to the container's `.bashrc`.
