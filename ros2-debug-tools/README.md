# ROS2 Debug Tools: Debugging Dashboard

This ROS2 package, `ros2_debug_dashboard`, provides a Python-based debugging dashboard. It includes nodes to monitor ROS2 topics, services, and logs. While full RViz integration for a custom dashboard is complex and typically involves plugins, this package will focus on providing command-line and potentially simple GUI (e.g., Tkinter, PlotJuggler integration concepts) tools for monitoring, with hooks or data streams that *could* be visualized in RViz if a suitable display plugin were used or developed.

## Features

-   **Topic Monitor:**
    -   Node to subscribe to a specified topic.
    -   Displays message content, frequency, and other statistics.
    -   Configurable topic and message type.
-   **Service Monitor:**
    -   Node to list available services.
    -   Attempts to call a specified service with given or default request data.
    -   Displays service response and call status.
-   **Log Monitor:**
    -   Node to subscribe to `/rosout` (ROS2 log messages).
    -   Filters and displays logs based on severity level (DEBUG, INFO, WARN, ERROR, FATAL).
    -   Highlights or counts error messages.
-   **RViz Integration (Conceptual):**
    -   Outputs data (e.g., topic rates, error counts) on topics that can be visualized in RViz using standard markers or potentially custom plugins (custom plugin development is outside the scope of this initial package).
    -   For example, publishing `std_msgs/Float32` for topic rates, which can be plotted in RViz with `rviz_plugin_plotjuggler` or similar.

## Prerequisites

-   ROS2 (Jazzy Jalisco recommended).
-   Python 3.
-   (Optional) For advanced GUI or plotting:
    -   `rqt_gui` and associated plugins.
    -   `plotjuggler-ros-plugins` for RViz plotting of time series data.

## Package Structure

```
ros2-debug-tools/
├── ros2_debug_dashboard/
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── ros2_debug_dashboard (empty marker file)
│   ├── ros2_debug_dashboard/
│   │   ├── __init__.py
│   │   ├── topic_monitor_node.py
│   │   ├── service_monitor_node.py
│   │   ├── log_monitor_node.py
│   │   └── (future: rviz_data_publisher_node.py)
│   ├── launch/
│   │   ├── start_topic_monitor.launch.py
│   │   ├── start_service_monitor.launch.py
│   │   ├── start_log_monitor.launch.py
│   │   └── (future: start_full_dashboard.launch.py)
│   ├── rviz/ (if specific RViz configs are provided)
│   │   └── debug_dashboard.rviz
│   └── test/
│       ├── test_copyright.py
│       ├── test_flake8.py
│       └── test_pep257.py
└── README.md
```

## Setup & Build

1.  **Navigate to your ROS2 workspace's `src` directory:**
    ```bash
    cd ~/your_ros2_workspace/src
    ```

2.  **Clone this repository (or copy `ros2_debug_dashboard` into `src`):**
    ```bash
    # git clone <this-repo-url>
    # mv ros2-debug-tools/ros2_debug_dashboard .
    # rm -rf ros2-debug-tools
    ```
    Ensure the `ros2_debug_dashboard` folder is inside your `src` directory.

3.  **Install dependencies (if any beyond standard ROS2):**
    ```bash
    cd ~/your_ros2_workspace
    rosdep install --from-paths src -y --ignore-src
    # Potentially install PlotJuggler for RViz plotting:
    # sudo apt-get install ros-jazzy-plotjuggler-ros-plugins
    ```

4.  **Build the workspace:**
    ```bash
    cd ~/your_ros2_workspace
    colcon build --symlink-install --packages-select ros2_debug_dashboard
    ```

5.  **Source the workspace:**
    ```bash
    source ~/your_ros2_workspace/install/setup.bash
    ```

## Usage

Make sure you have sourced your workspace in every new terminal.

### 1. Topic Monitor Node

Monitors a specified topic.

**Launch file:**
```bash
ros2 launch ros2_debug_dashboard start_topic_monitor.launch.py topic_name:=/your/topic message_type_pkg:=std_msgs message_type_name:=String
```
Replace `/your/topic`, `std_msgs`, and `String` with the actual topic name and message type package and name you want to monitor. The message type parts are used to dynamically import the correct type.

**Directly running the node:**
```bash
ros2 run ros2_debug_dashboard topic_monitor --ros-args -p topic_name:=/your/topic -p message_type_pkg:=std_msgs -p message_type_name:=String
```

The node will print information about received messages, frequency, etc., to the console.

### 2. Service Monitor Node

Lists available services or calls a specific service.

**Launch file (example to list services):**
```bash
# This launch file might just start the node which then requires CLI interaction or parameters for specific actions
ros2 launch ros2_debug_dashboard start_service_monitor.launch.py
```

**Directly running the node:**
-   **List all services:**
    ```bash
    ros2 run ros2_debug_dashboard service_monitor --ros-args -p action:=list
    ```
-   **Call a service (example: `/add_two_ints` of type `example_interfaces/srv/AddTwoInts`):**
    ```bash
    ros2 run ros2_debug_dashboard service_monitor --ros-args \
        -p action:=call \
        -p service_name:=/add_two_ints \
        -p service_type_pkg:=example_interfaces \
        -p service_type_name:=AddTwoInts \
        -p request_data:="{'a': 5, 'b': 10}"
    ```
    The `request_data` should be a Python dictionary string. The node will attempt to parse it and fill the request.

### 3. Log Monitor Node

Monitors `/rosout` for log messages and filters them.

**Launch file:**
```bash
ros2 launch ros2_debug_dashboard start_log_monitor.launch.py log_level:=INFO
```
Change `log_level` to `DEBUG`, `WARN`, `ERROR`, `FATAL` as needed.

**Directly running the node:**
```bash
ros2 run ros2_debug_dashboard log_monitor --ros-args -p log_level:=INFO
```

### RViz Integration (Conceptual)

If `rviz_data_publisher_node.py` is implemented, it would publish specific metrics (e.g., number of errors from log_monitor, rate of a topic from topic_monitor) as simple message types (like `std_msgs/Float32`) on dedicated topics.

These topics can then be visualized in RViz:
1.  Ensure `plotjuggler-ros-plugins` is installed.
2.  Open RViz: `rviz2`
3.  Add a "Plot" display type (from PlotJuggler Rviz Plugin).
4.  Configure the "Plot" display to subscribe to the topics published by `rviz_data_publisher_node.py`.

A sample `debug_dashboard.rviz` configuration could be provided to pre-configure these displays.

## Node Details

-   **`topic_monitor_node.py`**:
    -   Subscribes to a user-specified topic.
    -   Calculates and displays message rate, average message size (if feasible), and a sample of message contents.
    -   Uses dynamic message type importing based on parameters.
-   **`service_monitor_node.py`**:
    -   Lists available services and their types.
    -   Can attempt to call a specified service with a JSON/YAML string representing the request.
    -   Uses dynamic service type importing.
-   **`log_monitor_node.py`**:
    -   Subscribes to `/rosout` (type `rcl_interfaces/msg/Log`).
    -   Filters messages by severity level.
    -   Can count occurrences of specific error messages or patterns.

## Future Enhancements

-   A simple Tkinter or web-based GUI to consolidate the outputs.
-   More sophisticated RViz integration with custom display types (requires C++ plugin development).
-   Publishing aggregated statistics on topics for easier integration with other tools or RViz.
-   Action monitoring.
-   Parameter monitoring.
```
