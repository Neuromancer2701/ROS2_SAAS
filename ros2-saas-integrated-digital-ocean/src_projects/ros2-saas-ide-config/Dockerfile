# Base image: ROS2 Jazzy Jalisco
FROM ros:jazzy-ros-base

# Set noninteractive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential packages
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    python3-vcstool \
    wget \
    # ROS2 C++ and Python tools
    ros-jazzy-ament-cmake \
    ros-jazzy-ament-cmake-gtest \
    ros-jazzy-ament-lint-auto \
    ros-jazzy-ament-lint-common \
    ros-jazzy-ament-python \
    # Gazebo
    ros-jazzy-gazebo-ros-pkgs \
    # RViz
    ros-jazzy-rviz2 \
    ros-jazzy-rviz-default-plugins \
    # OpenCV
    libopencv-dev \
    python3-opencv \
    ros-jazzy-cv-bridge \
    # Other useful tools
    terminator \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN rosdep init && rosdep update

# Setup ROS environment
ENV ROS_DISTRO=jazzy
COPY ./ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]

# Create a ROS2 workspace
RUN mkdir -p /ros2_ws/src

# Copy workspace initialization script
COPY ./init_workspace.sh /ros2_ws/init_workspace.sh
RUN chmod +x /ros2_ws/init_workspace.sh

WORKDIR /ros2_ws
