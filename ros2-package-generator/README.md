# ROS2 Package Generator

This tool provides Python scripts to generate ROS2 package templates for both C++ (ament_cmake) and Python (ament_python) environments. It includes templates for common ROS2 node types: publisher, subscriber, service server/client, and action server/client. A Command Line Interface (CLI) tool is provided to automate the package creation process.

## Features

-   Generates ROS2 package structures for C++ and Python.
-   Templates for:
    -   Publisher node
    -   Subscriber node
    -   Service server node
    -   Service client node (as part of the service server template or standalone)
    -   Action server node
    -   Action client node (as part of the action server template or standalone)
-   CLI tool for easy package generation.
-   Customizable package name, node name, and topic/service/action names.

## Prerequisites

-   Python 3.6+
-   ROS2 installed (to ensure generated packages are compatible, though ROS2 is not strictly required to run the generator script itself).

## Installation / Setup

1.  **Clone the repository (or download the scripts):**
    ```bash
    # git clone <repository-url>
    # cd ros2-package-generator
    ```

2.  **Make the CLI tool executable (if not already):**
    ```bash
    chmod +x src/ros2_pkg_gen.py
    ```

## Usage

The main CLI tool is `ros2_pkg_gen.py`. You can run it with Python:

```bash
python3 src/ros2_pkg_gen.py <language> <package_name> <node_type> [options]
```

Or, if executable and in your PATH (or using a relative path):

```bash
./src/ros2_pkg_gen.py <language> <package_name> <node_type> [options]
```

### Arguments

-   `<language>`: The programming language for the package.
    -   `cpp` for C++ (ament_cmake)
    -   `py` for Python (ament_python)
-   `<package_name>`: The desired name for your new ROS2 package (e.g., `my_robot_controller`).
-   `<node_type>`: The type of ROS2 node template to generate.
    -   `publisher`
    -   `subscriber`
    -   `service_server` (generates a service server)
    -   `service_client` (generates a service client)
    -   `action_server` (generates an action server)
    -   `action_client` (generates an action client)

### Options

-   `--node-name <name>`: Specify the name for the node (e.g., `simple_publisher_node`). Defaults to `<package_name>_<node_type>_node`.
-   `--topic-name <name>`: For publisher/subscriber, the topic name. Defaults to `topic`.
-   `--service-name <name>`: For service server/client, the service name. Defaults to `service`.
-   `--action-name <name>`: For action server/client, the action name. Defaults to `action`.
-   `--target-path <path>`: The directory where the package will be created. Defaults to the current directory. The package will be created as a subdirectory (e.g., `<target-path>/<package_name>`).
-   `--msg-type <type>`: (Optional) For publisher/subscriber, specify the message type (e.g., `std_msgs/msg/Int32`). Defaults to `std_msgs/msg/String`.
-   `--srv-type <type>`: (Optional) For service server/client, specify the service type (e.g., `example_interfaces/srv/AddTwoInts`). Defaults to a custom `CustomSrv.srv` within the package.
-   `--action-type <type>`: (Optional) For action server/client, specify the action type (e.g., `action_tutorials_interfaces/action/Fibonacci`). Defaults to a custom `CustomAction.action` within the package.

### Examples

1.  **Create a C++ publisher package:**
    ```bash
    python3 src/ros2_pkg_gen.py cpp my_cpp_publisher publisher --node-name talker --topic-name chatter --msg-type std_msgs/msg/String --target-path ~/ros2_workspaces/dev_ws/src
    ```
    This will create a package `my_cpp_publisher` in `~/ros2_workspaces/dev_ws/src/my_cpp_publisher`.

2.  **Create a Python subscriber package in the current directory:**
    ```bash
    python3 src/ros2_pkg_gen.py py my_py_subscriber subscriber --node-name listener --topic-name chatter
    ```

3.  **Create a C++ service server package with a custom service name:**
    ```bash
    python3 src/ros2_pkg_gen.py cpp my_cpp_service service_server --service-name compute_sum --srv-type example_interfaces/srv/AddTwoInts
    ```

4.  **Create a Python action client:**
    ```bash
    python3 src/ros2_pkg_gen.py py my_py_action_client action_client --action-name fibonacci --action-type action_tutorials_interfaces/action/Fibonacci
    ```

## Generated Package Structure

The tool will generate a standard ROS2 package structure.

**For C++ (ament_cmake):**
```
<package_name>/
├── CMakeLists.txt
├── package.xml
├── include/
│   └── <package_name>/
│       └── (header files if any, e.g., node_class.hpp)
├── src/
│   └── (source files, e.g., node_executable.cpp)
├── srv/ (if service type is custom and generated)
│   └── CustomSrv.srv
└── action/ (if action type is custom and generated)
    └── CustomAction.action
```

**For Python (ament_python):**
```
<package_name>/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── <package_name> (empty marker file)
├── <package_name>/
│   ├── __init__.py
│   └── (python modules, e.g., node_script.py)
├── test/
│   ├── test_copyright.py
│   ├── test_flake8.py
│   └── test_pep257.py
├── srv/ (if service type is custom and generated)
│   └── CustomSrv.srv
└── action/ (if action type is custom and generated)
    └── CustomAction.action
```

## Templates

The generator uses internal string templates for various files. These templates are populated based on the user's input.
(Details about the specific template files and their content will be in the `src/templates/` directory or embedded within the generator script).

## Future Enhancements

-   Support for generating launch files.
-   Support for generating component nodes.
-   More complex node examples.
-   Interactive mode for CLI.
```
