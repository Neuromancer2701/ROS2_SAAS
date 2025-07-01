import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Optional: Path to custom slam_toolbox parameters file
    # slam_params_file_path = os.path.join(
    #     get_package_share_directory('tb3_simulation_pkg'),
    #     'config', 'slam_toolbox_params.yaml'
    # )

    # slam_toolbox node
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node', # For online SLAM
        # executable='sync_slam_toolbox_node', # For offline/batch SLAM
        name='slam_toolbox',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            # Optionally, load parameters from a YAML file:
            # slam_params_file_path
            # Or set parameters directly:
            {'odom_frame': 'odom'},
            {'map_frame': 'map'},
            {'base_frame': 'base_footprint'}, # base_footprint for TurtleBot3
            {'scan_topic': '/scan'},
            {'mode': 'mapping'}, # 'localization' or 'mapping'
            # {'map_file_name': 'my_map_name'}, # For localization mode, specify map to load
            # {'map_start_at_dock' : False}, # If you have a dock for the robot
            {'debug_logging': False},
            {'throttle_scans': 1}, # Process every Nth scan
            {'transform_timeout': 0.2},
            {'map_update_interval': 5.0}, # Seconds
            # Add more slam_toolbox parameters as needed, consult its documentation
            # For example, for specific sensor setups or performance tuning:
            # 'scan_queue_size': 2,
            # 'map_resolution': 0.05, # meters
            # 'max_laser_range': 8.0, # meters
        ],
        # remappings=[ # Default remappings are usually fine
        #     ('/scan', '/scan'),
        #     ('/tf', 'tf'),
        #     ('/map', 'map')
        # ]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true for SLAM processing'
        ),
        # DeclareLaunchArgument( # If using params file
        #     'slam_params_file',
        #     default_value=slam_params_file_path,
        #     description='Full path to the ROS2 parameters file to use for the slam_toolbox node'
        # ),
        slam_toolbox_node
    ])
