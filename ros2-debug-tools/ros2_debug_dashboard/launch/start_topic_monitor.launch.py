from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'topic_name',
            default_value='/chatter', # Example default
            description='The topic to monitor.'
        ),
        DeclareLaunchArgument(
            'message_type_pkg',
            default_value='std_msgs', # Example default
            description='Package of the message type (e.g., std_msgs).'
        ),
        DeclareLaunchArgument(
            'message_type_name',
            default_value='String', # Example default
            description='Name of the message type (e.g., String from std_msgs.msg).'
        ),
        DeclareLaunchArgument(
            'qos_depth',
            default_value='10',
            description='QoS history depth.'
        ),
        DeclareLaunchArgument(
            'qos_reliability',
            default_value='reliable',
            choices=['reliable', 'best_effort'],
            description='QoS reliability policy.'
        ),
        DeclareLaunchArgument(
            'qos_durability',
            default_value='volatile',
            choices=['volatile', 'transient_local'],
            description='QoS durability policy.'
        ),
        DeclareLaunchArgument(
            'display_interval_sec',
            default_value='5.0',
            description='Interval in seconds for displaying statistics.'
        ),
        DeclareLaunchArgument(
            'max_messages_to_display',
            default_value='3',
            description='Maximum number of message contents to display per interval.'
        ),

        Node(
            package='ros2_debug_dashboard',
            executable='topic_monitor',
            name='topic_monitor_node',
            output='screen',
            parameters=[{
                'topic_name': LaunchConfiguration('topic_name'),
                'message_type_pkg': LaunchConfiguration('message_type_pkg'),
                'message_type_name': LaunchConfiguration('message_type_name'),
                'qos_depth': LaunchConfiguration('qos_depth'),
                'qos_reliability': LaunchConfiguration('qos_reliability'),
                'qos_durability': LaunchConfiguration('qos_durability'),
                'display_interval_sec': LaunchConfiguration('display_interval_sec'),
                'max_messages_to_display': LaunchConfiguration('max_messages_to_display'),
            }]
        )
    ])
