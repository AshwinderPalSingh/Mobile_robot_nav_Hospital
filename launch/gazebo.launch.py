"""Bring up classic Gazebo 11 with the hospital ward world, spawn hospital_bot,
and publish its robot_state. Uses gazebo_ros (not Ignition/gz-sim) -- the
gazebo_ros_diff_drive and gazebo_ros_ray_sensor plugins publish cmd_vel/odom/
tf/scan directly as native ROS 2 topics, so no separate bridge node is needed."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory('hospital_delivery_bot')

    world_path = os.path.join(pkg_share, 'worlds', 'hospital_ward.world')
    xacro_path = os.path.join(pkg_share, 'urdf', 'hospital_bot.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_path]),
        value_type=str,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py',
            )
        ),
        launch_arguments={'world': world_path}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_hospital_bot',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'hospital_bot',
            # Offset off the walking_person's y=0 patrol line (see
            # worlds/hospital_ward.world) so spawning never overlaps the
            # actor's collision volume and gets shoved by the physics engine.
            '-x', '0',
            '-y', '-1.5',
            '-z', '0.2',
        ],
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
    ])
