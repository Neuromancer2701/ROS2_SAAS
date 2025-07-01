import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    # Directories
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_tb3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    pkg_this = get_package_share_directory('tb3_simulation_pkg')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='-2.0')
    y_pose = LaunchConfiguration('y_pose', default='-0.5')
    model = LaunchConfiguration('model', default='burger') # burger, waffle, waffle_pi
    # world_name = LaunchConfiguration('world_name', default='turtlebot3_world.world') # From turtlebot3_gazebo
    world_name = LaunchConfiguration('world_name', default='turtlebot3_house.world') # A more complex one from turtlebot3_gazebo

    # Paths
    # Use a world from turtlebot3_gazebo or a custom one from this package
    # world_path = PathJoinSubstitution([pkg_tb3_gazebo, 'worlds', world_name])
    # Example for custom world from this package:
    # world_path = PathJoinSubstitution([pkg_this, 'worlds', 'my_custom_world.world'])
    world_path = PathJoinSubstitution([pkg_tb3_gazebo, 'worlds', world_name])


    # Gazebo server and client
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world_path, 'verbose': 'false'}.items(),
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        ),
    )

    # Robot State Publisher
    # Uses the URDF from turtlebot3_description (pulled in by turtlebot3_gazebo)
    urdf_file_name = LaunchConfiguration('urdf_file_name', default='turtlebot3_' + model.perform(LaunchDescription().context) + '.urdf')
    urdf_path = PathJoinSubstitution([pkg_tb3_gazebo, 'urdf', urdf_file_name])

    # Need to ensure the model name in urdf_file_name is evaluated correctly.
    # A bit tricky with LaunchConfiguration directly in string concat for default.
    # Better to select URDF based on model argument.
    # For simplicity, we assume turtlebot3_gazebo handles this when spawning.
    # The robot_state_publisher here is for the /tf topic from /joint_states.

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': PathJoinSubstitution([pkg_tb3_gazebo, 'urdf', 'turtlebot3_', model, '.urdf'])
        }],
        #remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')] # default remappings are usually fine
    )

    # Spawn TurtleBot3
    # The turtlebot3_gazebo spawn_turtlebot3.launch.py handles finding the correct URDF
    # based on the 'model' argument and spawns it.
    spawn_turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_tb3_gazebo, 'launch', 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
            'model': model,
            'urdf_file_name': urdf_file_name # Pass it along, though spawn_turtlebot3 might derive it again
        }.items()
    )


    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        DeclareLaunchArgument(
            'x_pose',
            default_value='-2.0',
            description='Initial X pose of the robot'
        ),
        DeclareLaunchArgument(
            'y_pose',
            default_value='-0.5',
            description='Initial Y pose of the robot'
        ),
        DeclareLaunchArgument(
            'model',
            default_value='burger',
            choices=['burger', 'waffle', 'waffle_pi'],
            description='TurtleBot3 model type'
        ),
        DeclareLaunchArgument(
            'world_name',
            # default_value='turtlebot3_world.world',
            default_value='turtlebot3_house.world',
            description='Gazebo world file name from turtlebot3_gazebo/worlds or tb3_simulation_pkg/worlds'
        ),
        # DeclareLaunchArgument( # urdf_file_name is derived, not set directly by user usually
        #     'urdf_file_name',
        #     default_value='turtlebot3_burger.urdf', # Will be updated by model
        #     description='URDF file name for the robot model'
        # ),

        gzserver_cmd,
        gzclient_cmd,
        robot_state_publisher_node, # Publishes transforms based on joint states
        spawn_turtlebot_cmd,      # Spawns the robot model in Gazebo
    ])
