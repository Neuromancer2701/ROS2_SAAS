import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, select, termios, tty # For Linux keyboard input

# This is a basic Python teleoperation node.
# It's provided as an example within the package structure.
# The `teleop_keyboard.launch.py` file is configured to use
# the standard `teleop_twist_keyboard` package by default,
# as it's more robust and feature-rich.

# You can switch the launch file to use this node if you prefer,
# or run this node directly using `ros2 run tb3_simulation_pkg teleop_node_py`.

msg = """
Control Your TurtleBot3!
---------------------------
Moving around:
        w
   a    s    d
        x

w/x : increase/decrease linear velocity
a/d : increase/decrease angular velocity

space key, s : force stop

CTRL-C to quit
"""

move_bindings = {
    'w': (1, 0),  # Forward
    'x': (-1, 0), # Backward
    'a': (0, 1),  # Turn left
    'd': (0, -1), # Turn right
}

speed_bindings = {
    # Add bindings for speed changes if desired, e.g., q/e for linear, z/c for angular
}

class TeleopNodePy(Node):
    def __init__(self):
        super().__init__('teleop_node_py')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.settings = termios.tcgetattr(sys.stdin)

        self.speed = 0.1  # Linear speed
        self.turn = 0.5   # Angular speed
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0
        self.status = 0.0

        self.get_logger().info(msg)
        self.timer = self.create_timer(0.1, self.publish_twist) # Publish commands periodically

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1) # Timeout of 0.1s
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def vels(self, speed, turn):
        return "currently:\tspeed %s\tturn %s " % (speed, turn)

    def publish_twist(self):
        key = self.getKey()
        if key: # If a key was pressed
            if key in move_bindings.keys():
                self.x = move_bindings[key][0]
                self.th = move_bindings[key][1]
            elif key == ' ' or key == 's':
                self.x = 0.0
                self.th = 0.0
            elif key == '\x03': # CTRL-C
                # This will be caught by rclpy.spin() KeyboardInterrupt
                pass
            else: # If no valid move key, reset. This helps stop if a non-move key is hit.
                self.x = 0.0
                self.th = 0.0


            # Update status message (optional)
            if (self.status == 14):
                self.get_logger().info(msg)
            self.status = (self.status + 1) % 15
            # self.get_logger().info(self.vels(self.speed * self.x, self.turn * self.th))


        twist = Twist()
        twist.linear.x = self.x * self.speed
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = self.th * self.turn
        self.publisher_.publish(twist)


    def restore_terminal_settings(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNodePy()
    try:
        # No explicit rclpy.spin(node) here because getKey and publish_twist form the loop
        # However, for proper node lifecycle and executor handling, spin is better.
        # The timer callback will be executed by the spinner.
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('KeyboardInterrupt, shutting down.')
    except Exception as e:
        node.get_logger().error(f"An error occurred: {e}")
    finally:
        # Stop the robot before exiting
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        node.publisher_.publish(twist)
        # Restore terminal settings
        node.restore_terminal_settings()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
