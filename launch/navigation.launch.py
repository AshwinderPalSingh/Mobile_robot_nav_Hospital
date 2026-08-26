"""Nav2 autonomous navigation launch for hospital_bot.

Starts:
  - Gazebo  (world + robot + diff-drive + lidar via gazebo.launch.py)
  - map_server   (serves the PGM map produced by SLAM)
  - amcl          (Monte-Carlo localisation against the static map)
  - nav2_bringup  (planner, controller, behaviour trees, costmaps ...)
  - RViz          (Nav2 preset with 2D-Goal-Pose tool enabled)
  - lifecycle_manager (brings up map_server + amcl + nav2 nodes)

Usage
-----
  # Terminal 1 - start everything
  ros2 launch hospital_delivery_bot navigation.launch.py

  # In RViz: click "2D Goal Pose" on the toolbar, then click on the map.
  # Nav2 will plan and drive the robot autonomously.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('hospital_delivery_bot')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # --------------- launch arguments ----------------------------------------
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation (Gazebo) clock'
    )
    map_yaml_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_share, 'maps', 'hospital_ward.yaml'),
        description='Full path to the map yaml file to load'
    )
    nav2_params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_share, 'config', 'nav2_params.yaml'),
        description='Full path to the Nav2 parameter file'
    )
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(pkg_share, 'config', 'rviz_config.rviz'),
        description='Full path to the RViz config file'
    )
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Whether to launch RViz'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml     = LaunchConfiguration('map')
    params_file  = LaunchConfiguration('params_file')
    rviz_config  = LaunchConfiguration('rviz_config')
    use_rviz     = LaunchConfiguration('use_rviz')

    # --------------- Gazebo + robot ------------------------------------------
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gazebo.launch.py')
        )
    )

    # --------------- Nav2 bringup --------------------------------------------
    # nav2_bringup's bringup_launch.py starts map_server, amcl, planner,
    # controller, bt_navigator, behaviour_server, waypoint_follower, and all
    # associated lifecycle managers in one shot.
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map':          map_yaml,
            'params_file':  params_file,
            # autostart = true so you do not have to call lifecycle transitions
            # manually before sending a nav goal.
            'autostart':    'true',
        }.items(),
    )

    # --------------- RViz ----------------------------------------------------
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        use_sim_time_arg,
        map_yaml_arg,
        nav2_params_arg,
        rviz_config_arg,
        use_rviz_arg,
        gazebo,
        nav2_bringup,
        rviz,
    ])
