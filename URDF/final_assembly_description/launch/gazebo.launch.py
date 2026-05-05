import os
from ament_index_python.packages import get_package_share_directory #type: ignore
from launch import LaunchDescription #type: ignore
from launch.actions import IncludeLaunchDescription #type: ignore
from launch.launch_description_sources import PythonLaunchDescriptionSource #type: ignore
from launch_ros.actions import Node #type: ignore
import xacro #type: ignore

def generate_launch_description():
    pkg_name = 'final_assembly_description'
    pkg_dir = get_package_share_directory(pkg_name)
    
    # Process the URDF file
    xacro_file = os.path.join(pkg_dir, 'urdf', 'final_assembly.xacro')
    doc = xacro.process_file(xacro_file)
    robot_description = {'robot_description': doc.toxml()}
    
    # Path to the world file
    world_file_name = 'warehouse.world'
    world_path = os.path.join(pkg_dir, 'worlds', world_file_name)

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
        launch_arguments={'world': world_path}.items()
    )

    # Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}]
    )

    # Spawn Robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description',
                   '-entity', 'firefighting_robot',
                   '-z', '0.1'], # Spawn slightly above ground
        output='screen'
    )

    # Spawn Nozzle Controller
    spawn_nozzle_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['nozzle_velocity_controller'],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        spawn_nozzle_controller
    ])
