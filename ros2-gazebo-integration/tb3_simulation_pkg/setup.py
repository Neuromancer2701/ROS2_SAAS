from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'tb3_simulation_pkg'

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
        # World files
        (os.path.join('share', package_name, 'worlds'), glob(os.path.join('worlds', '*.world'))),
        (os.path.join('share', package_name, 'worlds'), glob(os.path.join('worlds', '*.model'))), # If you use .model files for worlds
        # RViz configuration files
        (os.path.join('share', package_name, 'rviz'), glob(os.path.join('rviz', '*.rviz'))),
        # URDF/XACRO files if any (not typical for this package as it uses turtlebot3_gazebo)
        # (os.path.join('share', package_name, 'urdf'), glob(os.path.join('urdf', '*.*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='user@todo.todo',
    description='ROS2 package for TurtleBot3 Gazebo simulation, teleoperation, and SLAM.',
    license='Apache License 2.0', # Or your chosen license
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleop_node_py = tb3_simulation_pkg.teleop_node:main',
            # Add other Python executables here
        ],
    },
)
