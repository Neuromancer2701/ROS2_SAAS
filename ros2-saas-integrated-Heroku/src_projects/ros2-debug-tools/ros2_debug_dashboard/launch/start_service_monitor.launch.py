from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'action',
            default_value='list', # 'list' or 'call'
            choices=['list', 'call'],
            description='Action to perform: list services or call a specific service.'
        ),
        DeclareLaunchArgument(
            'service_name',
            default_value='', # Example: /add_two_ints
            description='Name of the service to call (required if action is "call").'
        ),
        DeclareLaunchArgument(
            'service_type_pkg',
            default_value='', # Example: example_interfaces
            description='Package of the service type (required if action is "call").'
        ),
        DeclareLaunchArgument(
            'service_type_name',
            default_value='', # Example: AddTwoInts (from <pkg>.srv)
            description='Name of the service type (required if action is "call").'
        ),
        DeclareLaunchArgument(
            'request_data',
            default_value='{}', # JSON string
            description='JSON string representing the request data (for "call" action).'
        ),
        DeclareLaunchArgument(
            'timeout_sec',
            default_value='5.0',
            description='Timeout in seconds for waiting for service or service call completion.'
        ),

        Node(
            package='ros2_debug_dashboard',
            executable='service_monitor',
            name='service_monitor_node',
            output='screen',
            parameters=[{
                'action': LaunchConfiguration('action'),
                'service_name': LaunchConfiguration('service_name'),
                'service_type_pkg': LaunchConfiguration('service_type_pkg'),
                'service_type_name': LaunchConfiguration('service_type_name'),
                'request_data': LaunchConfiguration('request_data'),
                'timeout_sec': LaunchConfiguration('timeout_sec'),
            }]
            # The service_monitor_node is designed to exit after performing its action.
            # If you want it to stay alive for other reasons, you might need to adjust its internal logic.
        )
    ])
