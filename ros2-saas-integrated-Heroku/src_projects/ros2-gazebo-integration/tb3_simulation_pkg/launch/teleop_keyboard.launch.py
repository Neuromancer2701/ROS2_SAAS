from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Launch argument for use_sim_time
    use_sim_time = LaunchConfiguration('use_sim_time', default='true') # Default to true as we are in simulation

    # Node for teleop_twist_keyboard
    teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        prefix='xterm -e',  # Opens in a new xterm window, making it easy to focus for keyboard input
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('/cmd_vel', '/cmd_vel') # Default mapping, explicitly stated for clarity
        ]
    )

    # Node for the custom Python teleop node (if you want to use it instead)
    # Ensure 'teleop_node_py' is defined in your setup.py entry_points
    # custom_teleop_node = Node(
    #     package='tb3_simulation_pkg',
    #     executable='teleop_node_py',
    #     name='custom_teleop_node',
    #     output='screen',
    #     prefix='xterm -e',
    #     parameters=[{'use_sim_time': use_sim_time}]
    # )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        teleop_node,
        # custom_teleop_node, # Uncomment to use your custom Python teleop node
    ])
