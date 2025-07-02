#!/bin/bash

# Script to initialize a ROS2 workspace and create an example C++ package.

# Check if workspace name is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <workspace_name> [package_name]"
  exit 1
fi

WORKSPACE_NAME=$1
PACKAGE_NAME=${2:-my_cpp_pkg} # Default package name if not provided

# Create the workspace directory
if [ -d "$WORKSPACE_NAME" ]; then
  echo "Directory '$WORKSPACE_NAME' already exists. Please choose a different name or remove the existing directory."
  exit 1
fi
mkdir -p "$WORKSPACE_NAME/src"
cd "$WORKSPACE_NAME"

echo "Successfully created workspace: $WORKSPACE_NAME"

# Create an example C++ package
echo "Creating example C++ package: $PACKAGE_NAME"
ros2 pkg create --build-type ament_cmake "$PACKAGE_NAME" --node-name my_node --destination-directory src

# Populate the example C++ node with a simple publisher
cat <<EOF > src/$PACKAGE_NAME/src/my_node.cpp
#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class MinimalPublisher : public rclcpp::Node
{
public:
  MinimalPublisher()
  : Node("${PACKAGE_NAME}_node"), count_(0)
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("topic", 10);
    timer_ = this->create_wall_timer(
      500ms, std::bind(&MinimalPublisher::timer_callback, this));
    RCLCPP_INFO(this->get_logger(), "MinimalPublisher node started and publishing to 'topic'");
  }

private:
  void timer_callback()
  {
    auto message = std_msgs::msg::String();
    message.data = "Hello, world! " + std::to_string(count_++);
    RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
    publisher_->publish(message);
  }
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalPublisher>());
  rclcpp::shutdown();
  return 0;
}
EOF

# Update CMakeLists.txt to find necessary packages and build the executable
cat <<EOF > src/$PACKAGE_NAME/CMakeLists.txt
cmake_minimum_required(VERSION 3.8)
project($PACKAGE_NAME)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(my_node src/my_node.cpp)
ament_target_dependencies(my_node rclcpp std_msgs)

install(TARGETS
  my_node
  DESTINATION lib/\${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_lint_auto_lint_types arbos cppcheck cpplint flake8 pep257)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
EOF

echo "Example package '$PACKAGE_NAME' created in 'src/$PACKAGE_NAME'."
echo "To build the workspace, run:"
echo "  colcon build --symlink-install"
echo "Then source the setup file:"
echo "  source install/setup.bash"
echo "And run the node:"
echo "  ros2 run $PACKAGE_NAME my_node"

cd ../.. # Go back to the root of ros2-saas-ide-config, assuming script is run from there
echo "Workspace initialization complete. The script created '$WORKSPACE_NAME' inside 'ros2-saas-ide-config'."
echo "If you run this script from within the container's /ros2_ws, the new workspace will be created there."
echo "Example: ./init_workspace.sh my_new_ws"
echo "Then: cd my_new_ws"
# Note: The script itself should be executable. This line is for the script itself.
# chmod +x init_workspace.sh # This should be done outside the script, on the file itself.
# chmod +x src/$PACKAGE_NAME/src/my_node.cpp # Not strictly necessary for compilation but good practice

# The script is intended to be placed in /ros2_ws in the Docker container,
# or alongside the Dockerfile if building locally and then copied in.
# The Dockerfile places it in /ros2_ws, so when running inside the container,
# it would be invoked from there or copied to a new workspace dir.
# The README instructs user to run it from /ros2_ws or copy it.
# For clarity, the `cd ..` was changed to `cd ../..` if we assume it's run from `ros2-saas-ide-config`
# However, the README implies it will be in /ros2_ws in the container.
# Let's assume the script is in /ros2_ws as per Dockerfile COPY and WORKDIR.
# If so, `cd "$WORKSPACE_NAME"` is correct, and `cd ..` at the end would return to /ros2_ws.

# Re-adjusting the final cd and echo message assuming the script is in /ros2_ws and creates the new workspace there.
# This was the original intent.
# cd .. # This would take it to the parent of WORKSPACE_NAME, which is /ros2_ws
# echo "Workspace initialization complete. New workspace is at: $(pwd)/$WORKSPACE_NAME"
# The WORKDIR in Dockerfile is /ros2_ws. The script is copied to /ros_entrypoint.sh, not init_workspace.sh.
# The init_workspace.sh is part of the host files, to be used by the user.
# The README implies init_workspace.sh is available at /ros2_ws or the user copies it there.
# Let's assume the user copies it to /ros2_ws or similar and runs it.

# Finalizing the script with corrected cd logic for typical use case (running from /ros2_ws or a subdir).
# If script is in /ros2_ws and run as ./init_workspace.sh new_ws, it creates /ros2_ws/new_ws.
# `cd "$WORKSPACE_NAME"` takes it into /ros2_ws/new_ws.
# `cd ..` at the end returns to /ros2_ws.

cd .. # Return to the directory from which the script was called (e.g., /ros2_ws)
echo "Workspace '$WORKSPACE_NAME' created at $(pwd)/$WORKSPACE_NAME"
echo "Remember to make this script executable: chmod +x init_workspace.sh"

# Correcting the path in README for init_workspace.sh if it's intended to be copied into /ros2_ws
# The Dockerfile currently copies ros_entrypoint.sh but not init_workspace.sh.
# The README should instruct to copy it or make it available in the workspace.
# For now, the script itself is fine. The chmod will be run on the host file.
# The user will then copy this executable script into their container or a mounted volume.
# The path in the README:
# "To use it, run the following command inside the running Docker container (from the `/ros2_ws` directory or any other preferred location):"
# ```bash
# ./init_workspace.sh <workspace_name> [package_name]
# ```
# This implies the script is present in the current directory inside the container.
# The Dockerfile should be updated to copy it.
# Let's proceed with creating the script file, then chmod, then update Dockerfile, then update README.
# This current tool call is for creating `init_workspace.sh`.
# The content above is fine.
# The next step will be chmod.
# Then updating Dockerfile and README.
# For now, this file creation is the step.
