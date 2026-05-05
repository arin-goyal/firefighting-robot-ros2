import os
from ament_index_python.packages import get_package_share_directory #type: ignore
from launch import LaunchDescription #type: ignore
from launch.actions import DeclareLaunchArgument #type: ignore
from launch.substitutions import LaunchConfiguration #type: ignore
from launch_ros.actions import Node #type: ignore
import xacro #type: ignore

def generate_launch_description():
    # Get the package directory
    pkg_dir = get_package_share_directory('final_assembly_description')
    
    # Process the URDF file
    xacro_file = os.path.join(pkg_dir, 'urdf', 'final_assembly.xacro')
    doc = xacro.process_file(xacro_file)
    robot_description = {'robot_description': doc.toxml()}
    
    # Path to the RViz config
    rviz_config_file = os.path.join(pkg_dir, 'launch', 'urdf.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_description, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
        ),
        
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen'
        ),
        
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file]
        )
    ])
