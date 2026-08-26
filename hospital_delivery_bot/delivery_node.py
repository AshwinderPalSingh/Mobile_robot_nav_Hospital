#!/usr/bin/env python3
"""Placeholder delivery node — Nav2 action-client delivery logic goes here."""

import rclpy
from rclpy.node import Node


class DeliveryNode(Node):
    def __init__(self):
        super().__init__('delivery_node')
        self.get_logger().info('delivery_node started (stub — no delivery logic yet)')


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
