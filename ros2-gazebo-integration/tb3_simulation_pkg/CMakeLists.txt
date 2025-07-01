cmake_minimum_required(VERSION 3.8)
project(tb3_simulation_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find necessary packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
# Add other C++ dependencies if you have C++ nodes that need them

# Example C++ node (if you have one)
# add_executable(teleop_node_cpp src/teleop_node.cpp)
# ament_target_dependencies(teleop_node_cpp rclcpp geometry_msgs)
# install(TARGETS
#   teleop_node_cpp
#   DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install world files (if any custom worlds are provided)
install(
  DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}/
  FILES_MATCHING PATTERN "*.model" PATTERN "*.world"
)

# Install RViz configuration files
install(
  DIRECTORY rviz
  DESTINATION share/${PROJECT_NAME}/
  FILES_MATCHING PATTERN "*.rviz"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter tests
  # set(ament_lint_auto_skip TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
