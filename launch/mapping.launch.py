"""Master launch for the teleop SLAM mapping run:
Gazebo (world + robot + bridge) + slam_toolbox + RViz.

Teleop is intentionally NOT included here -- run it yourself in a separate
terminal so it has a real TTY for keyboard input:
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('hospital_delivery_bot')
    launch_dir = os.path.join(pkg_share, 'launch')
    rviz_config = os.path.join(pkg_share, 'config', 'rviz_config.rviz')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'gazebo.launch.py'))
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'slam.launch.py'))
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        gazebo,
        slam,
        rviz,
    ])
