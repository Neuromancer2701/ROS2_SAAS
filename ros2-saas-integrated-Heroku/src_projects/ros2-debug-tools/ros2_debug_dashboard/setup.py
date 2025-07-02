from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ros2_debug_dashboard'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch files
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
        # RViz configuration files (if any)
        (os.path.join('share', package_name, 'rviz'), glob(os.path.join('rviz', '*.rviz'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='user@todo.todo',
    description='A Python-based ROS2 debugging dashboard.',
    license='Apache License 2.0', # Or your chosen license
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'topic_monitor = ros2_debug_dashboard.topic_monitor_node:main',
            'service_monitor = ros2_debug_dashboard.service_monitor_node:main',
            'log_monitor = ros2_debug_dashboard.log_monitor_node:main',
            # 'rviz_data_publisher = ros2_debug_dashboard.rviz_data_publisher_node:main', # If implemented
        ],
    },
)
