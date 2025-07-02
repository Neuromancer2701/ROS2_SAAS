import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Path to the RViz configuration file
    rviz_config_file_name = 'slam_config.rviz' # Your custom RViz config for SLAM
    rviz_config_path = PathJoinSubstitution([
        get_package_share_directory('tb3_simulation_pkg'),
        'rviz',
        rviz_config_file_name
    ])

    # Default RViz configuration from nav2_bringup if you don't have a custom one yet
    # rviz_config_path_default = PathJoinSubstitution([
    #     get_package_share_directory('nav2_bringup'), # Depends on nav2_bringup being installed
    #     'rviz',
    #     'nav2_default_view.rviz'
    # ])


    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_slam',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        # remappings=[ # Optional remappings if topics differ
        #     ('/tf', 'tf'),
        #     ('/tf_static', 'tf_static'),
        #     # Add other remappings if your topics are different from what RViz expects by default
        # ]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true for RViz'
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=rviz_config_path,
            description='Full path to the RViz configuration file to use'
        ),
        rviz_node
    ])
