from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'log_level',
            default_value='INFO',
            choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
            description='Minimum log level to display (DEBUG, INFO, WARN, ERROR, FATAL).'
        ),

        Node(
            package='ros2_debug_dashboard',
            executable='log_monitor',
            name='log_monitor_node',
            output='screen', # Log messages will be printed to screen by the node's logger
            parameters=[{
                'log_level': LaunchConfiguration('log_level'),
            }]
        )
    ])
