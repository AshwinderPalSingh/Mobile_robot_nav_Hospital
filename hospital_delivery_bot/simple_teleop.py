#!/usr/bin/env python3
"""Simple arrow-key / WASD teleop -- publishes geometry_msgs/Twist to /cmd_vel.

Controls:
  Up / w      forward
  Down / s    backward
  Left / a    rotate left in place
  Right / d   rotate right in place
  k           stop
  + / -       increase / decrease speed
  q / Ctrl-C  quit

The robot keeps moving at the last commanded velocity until you press
another key -- press k to stop.

NOTE: space is deliberately NOT a stop key here. Gazebo's own GUI window
uses spacebar to pause/resume the whole simulation, and it's easy for
window focus to slip there -- an accidental space in Gazebo freezes
everything (looks like a crash, isn't one). Use k instead.
"""

import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

BANNER = """
Simple teleop -- arrow keys or WASD
------------------------------------
   Up / w     : forward
   Down / s   : backward
   Left / a   : rotate left
   Right / d  : rotate right
   k          : stop
   +          : speed up
   -          : slow down
   q          : quit
------------------------------------
"""

MOVE_BINDINGS = {
    'w': (1.0, 0.0),
    's': (-1.0, 0.0),
    'a': (0.0, 1.0),
    'd': (0.0, -1.0),
    'UP': (1.0, 0.0),
    'DOWN': (-1.0, 0.0),
    'LEFT': (0.0, 1.0),
    'RIGHT': (0.0, -1.0),
}

STOP_KEYS = ('k',)
QUIT_KEYS = ('q', '\x03')  # q or Ctrl-C


def read_key(settings):
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
    if ch == '\x1b':
        # Arrow keys arrive as ESC [ A/B/C/D
        rest = sys.stdin.read(2)
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
        arrow_map = {'A': 'UP', 'B': 'DOWN', 'C': 'RIGHT', 'D': 'LEFT'}
        return arrow_map.get(rest[-1], '')
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
    return ch


def main(args=None):
    rclpy.init(args=args)
    node = Node('simple_teleop')
    pub = node.create_publisher(Twist, 'cmd_vel', 10)

    settings = termios.tcgetattr(sys.stdin.fileno())
    linear_speed = 0.3
    angular_speed = 1.0
    lin_dir = 0.0
    ang_dir = 0.0

    print(BANNER)
    try:
        while rclpy.ok():
            key = read_key(settings)

            if key in QUIT_KEYS:
                break
            elif key in STOP_KEYS:
                lin_dir, ang_dir = 0.0, 0.0
            elif key in MOVE_BINDINGS:
                lin_dir, ang_dir = MOVE_BINDINGS[key]
            elif key == '+':
                linear_speed = min(linear_speed + 0.05, 1.0)
                angular_speed = min(angular_speed + 0.2, 3.0)
                print(f'speed: linear={linear_speed:.2f} angular={angular_speed:.2f}')
            elif key == '-':
                linear_speed = max(linear_speed - 0.05, 0.05)
                angular_speed = max(angular_speed - 0.2, 0.2)
                print(f'speed: linear={linear_speed:.2f} angular={angular_speed:.2f}')
            else:
                continue

            twist = Twist()
            twist.linear.x = lin_dir * linear_speed
            twist.angular.z = ang_dir * angular_speed
            pub.publish(twist)
    finally:
        pub.publish(Twist())  # stop the robot on exit
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
