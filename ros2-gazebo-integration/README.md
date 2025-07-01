# ROS2 Gazebo Integration for TurtleBot3

This ROS2 package provides launch files and nodes to simulate a TurtleBot3 robot in Gazebo. It includes examples for teleoperation (keyboard control) and running SLAM (Simultaneous Localization and Mapping) using the `slam_toolbox`.

## Features

-   Launch files to easily start Gazebo with a TurtleBot3 model (Burger, Waffle, or Waffle Pi).
-   Keyboard teleoperation node for manual control of the TurtleBot3 in simulation.
-   Integration with `slam_toolbox` for 2D SLAM.
-   RViz configuration for visualizing robot model, sensor data, and SLAM map.
-   Example C++ and Python nodes (basic publisher/subscriber can be adapted for teleop or other tasks).

## Prerequisites

-   ROS2 (Jazzy Jalisco recommended, tested with environment from `ros2-saas-ide-config`).
-   Gazebo (installed as part of `ros-jazzy-gazebo-ros-pkgs`).
-   `slam_toolbox` for ROS2 Jazzy:
    ```bash
    sudo apt-get update
    sudo apt-get install ros-jazzy-slam-toolbox
    ```
-   TurtleBot3 simulation packages for ROS2 Jazzy:
    ```bash
    sudo apt-get install ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3-teleop ros-jazzy-turtlebot3-cartographer
    # Note: We use slam_toolbox, but cartographer is often bundled or useful for comparison.
    # The key package is turtlebot3_gazebo for models and worlds.
    ```
-   (Optional but recommended) `teleop_twist_keyboard` for generic keyboard teleop:
    ```bash
    sudo apt-get install ros-jazzy-teleop-twist-keyboard
    ```

## Package Structure

```
ros2-gazebo-integration/
├── tb3_simulation_pkg/
│   ├── package.xml
│   ├── CMakeLists.txt (if C++ nodes are used significantly)
│   ├── setup.py (if Python nodes are used significantly)
│   ├── launch/
│   │   ├── turtlebot3_world.launch.py  (Main launch file for Gazebo + Robot)
│   │   ├── teleop_keyboard.launch.py (Launch file for keyboard teleoperation)
│   │   ├── slam_toolbox.launch.py    (Launch file for SLAM)
│   │   └── rviz_slam.launch.py       (Launch RViz with SLAM config)
│   ├── worlds/
│   │   └── turtlebot3_world.model    (Example Gazebo world file, or use default ones)
│   ├── rviz/
│   │   └── slam_config.rviz          (RViz configuration for SLAM)
│   ├── src/ (for C++ nodes)
│   │   └── teleop_node.cpp           (Placeholder/Example C++ teleop logic)
│   └── tb3_simulation_pkg/ (for Python nodes)
│       └── teleop_node.py            (Python teleoperation node)
└── README.md
```

## Setup & Build

1.  **Navigate to your ROS2 workspace's `src` directory:**
    ```bash
    cd ~/your_ros2_workspace/src
    ```

2.  **Clone this package (or copy it) into the `src` directory:**
    If this `ros2-gazebo-integration` directory is the root of the repo containing `tb3_simulation_pkg`:
    ```bash
    # git clone <this-repo-url>
    # mv ros2-gazebo-integration/tb3_simulation_pkg .
    # rm -rf ros2-gazebo-integration
    ```
    Or, if `ros2-gazebo-integration` *is* the `tb3_simulation_pkg` (adjust as needed):
    ```bash
    # git clone <this-repo-url> ros2-gazebo-integration
    ```
    Essentially, ensure the `tb3_simulation_pkg` folder is inside your `src` directory.

3.  **Install dependencies (if not already installed):**
    ```bash
    cd ~/your_ros2_workspace
    rosdep install --from-paths src -y --ignore-src
    ```
    And ensure `slam_toolbox`, `turtlebot3_gazebo`, etc., are installed as per Prerequisites.

4.  **Build the workspace:**
    ```bash
    cd ~/your_ros2_workspace
    colcon build --symlink-install
    ```

5.  **Source the workspace:**
    ```bash
    source ~/your_ros2_workspace/install/setup.bash
    ```

## Execution Instructions

Make sure you have sourced your workspace in every new terminal.

### 1. Launch Gazebo with TurtleBot3

You can specify the TurtleBot3 model (burger, waffle, waffle_pi).
```bash
# Default model (burger)
ros2 launch tb3_simulation_pkg turtlebot3_world.launch.py

# Specify waffle_pi model
ros2 launch tb3_simulation_pkg turtlebot3_world.launch.py model:=waffle_pi
```
This will open Gazebo with the specified TurtleBot3 model in a predefined world (or the default TurtleBot3 world).

### 2. Launch Keyboard Teleoperation

Open a new terminal, source your workspace, and run:
```bash
# Using the provided Python teleop node (tb3_simulation_pkg.teleop_node)
ros2 launch tb3_simulation_pkg teleop_keyboard.launch.py

# OR, using the standard teleop_twist_keyboard (if installed and preferred)
# ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```
Follow the instructions in the terminal to control the robot with your keyboard. The terminal running the teleop node must be active (in focus).

### 3. Launch SLAM (slam_toolbox)

Open a new terminal, source your workspace, and run:
```bash
ros2 launch tb3_simulation_pkg slam_toolbox.launch.py
```
This will start the `slam_toolbox` node, which will process laser scan data and build a map.

### 4. Launch RViz for SLAM Visualization

Open another new terminal, source your workspace, and run:
```bash
ros2 launch tb3_simulation_pkg rviz_slam.launch.py
```
This will open RViz with a configuration suitable for visualizing the robot, laser scans, and the map being built by SLAM.

**Order of launching:**
1.  `turtlebot3_world.launch.py` (Gazebo simulation)
2.  (Optional) `teleop_keyboard.launch.py` (for manual control to explore and map)
3.  `slam_toolbox.launch.py` (SLAM node)
4.  `rviz_slam.launch.py` (Visualization)

Drive the robot around using the teleoperation node. You should see the map being generated in RViz.

## Node Details

### Teleoperation Node (`tb3_simulation_pkg/teleop_node.py`)

A simple Python node that listens to keyboard inputs (using `getch` or similar for non-blocking input if run directly, or use `teleop_twist_keyboard` for a more robust solution) and publishes `Twist` messages to the `/cmd_vel` topic. The launch file `teleop_keyboard.launch.py` typically uses `teleop_twist_keyboard` for better compatibility.

### C++ Example Node (`src/teleop_node.cpp`)

A placeholder or basic C++ node structure. For actual teleoperation, a more complex implementation would be needed, or one could use existing packages like `teleop_twist_keyboard`. This can be adapted for other tasks like simple sensor processing or control logic.

## Customization

-   **Robot Model:** Change the `model` argument in `turtlebot3_world.launch.py` (e.g., `model:=waffle`).
-   **Gazebo World:** Modify the `world` argument in `turtlebot3_world.launch.py` to use a different `.world` or `.model` file. You can create custom worlds and place them in the `worlds/` directory.
-   **RViz Configuration:** Customize `rviz/slam_config.rviz` to change visualization options.
-   **SLAM Parameters:** Adjust parameters for `slam_toolbox` in `slam_toolbox.launch.py` for different environments or performance tuning. Refer to the `slam_toolbox` documentation for details.
```
