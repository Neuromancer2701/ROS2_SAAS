import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import importlib
import time
import sys

class TopicMonitorNode(Node):
    def __init__(self):
        super().__init__('topic_monitor_node')

        self.declare_parameter('topic_name', '/default_topic')
        self.declare_parameter('message_type_pkg', 'std_msgs') # e.g., 'std_msgs'
        self.declare_parameter('message_type_name', 'String') # e.g., 'String' (from std_msgs.msg)
        self.declare_parameter('qos_depth', 10)
        self.declare_parameter('qos_reliability', 'reliable') # 'reliable' or 'best_effort'
        self.declare_parameter('qos_durability', 'volatile') # 'volatile' or 'transient_local'
        self.declare_parameter('display_interval_sec', 5.0) # How often to print stats
        self.declare_parameter('max_messages_to_display', 3) # Max messages to show content for per interval

        self.topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        self.message_type_pkg = self.get_parameter('message_type_pkg').get_parameter_value().string_value
        self.message_type_name = self.get_parameter('message_type_name').get_parameter_value().string_value
        self.qos_depth = self.get_parameter('qos_depth').get_parameter_value().integer_value
        qos_reliability_str = self.get_parameter('qos_reliability').get_parameter_value().string_value.upper()
        qos_durability_str = self.get_parameter('qos_durability').get_parameter_value().string_value.upper()
        self.display_interval = self.get_parameter('display_interval_sec').get_parameter_value().double_value
        self.max_messages_display = self.get_parameter('max_messages_to_display').get_parameter_value().integer_value


        self.get_logger().info(f"Attempting to monitor topic: '{self.topic_name}'")
        self.get_logger().info(f"Expected message type: '{self.message_type_pkg}.msg.{self.message_type_name}'")

        try:
            module = importlib.import_module(f"{self.message_type_pkg}.msg")
            self.msg_type = getattr(module, self.message_type_name)
        except ModuleNotFoundError:
            self.get_logger().error(f"Could not import message type module: {self.message_type_pkg}.msg")
            sys.exit(1)
        except AttributeError:
            self.get_logger().error(f"Could not find message type '{self.message_type_name}' in module '{self.message_type_pkg}.msg'")
            sys.exit(1)
        except Exception as e:
            self.get_logger().error(f"An unexpected error occurred during message type import: {e}")
            sys.exit(1)

        # Determine QoS settings
        reliability_policy = ReliabilityPolicy.RELIABLE if qos_reliability_str == 'RELIABLE' else ReliabilityPolicy.BEST_EFFORT
        durability_policy = DurabilityPolicy.TRANSIENT_LOCAL if qos_durability_str == 'TRANSIENT_LOCAL' else DurabilityPolicy.VOLATILE

        self.qos_profile = QoSProfile(
            reliability=reliability_policy,
            history=HistoryPolicy.KEEP_LAST,
            depth=self.qos_depth,
            durability=durability_policy
        )
        self.get_logger().info(f"Using QoS Profile: Reliability: {qos_reliability_str}, Durability: {qos_durability_str}, Depth: {self.qos_depth}")

        self.subscription = self.create_subscription(
            self.msg_type,
            self.topic_name,
            self.listener_callback,
            self.qos_profile
        )

        self.message_count = 0
        self.last_display_time = time.time()
        self.bytes_received = 0
        self.recent_messages_content = []

        self.timer = self.create_timer(self.display_interval, self.display_statistics)
        self.get_logger().info(f"Topic monitor started for '{self.topic_name}'. Displaying stats every {self.display_interval}s.")

    def listener_callback(self, msg):
        self.message_count += 1
        try:
            # A simple way to estimate message size; for complex types, this is very approximate.
            # A more accurate way would be to serialize the message and get its size.
            self.bytes_received += sys.getsizeof(msg)
        except Exception:
            # If sys.getsizeof fails for some complex types, fallback or ignore.
            # This is a basic monitor, so we don't want it to crash.
            pass

        if len(self.recent_messages_content) < self.max_messages_display:
            try:
                # Convert message to string for display. This might be long for complex messages.
                # Consider truncating or showing only specific fields for very large messages.
                msg_str = str(msg)
                if len(msg_str) > 200: # Truncate very long messages
                    msg_str = msg_str[:200] + "..."
                self.recent_messages_content.append(msg_str)
            except Exception as e:
                self.recent_messages_content.append(f"[Error converting msg to str: {e}]")


    def display_statistics(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_display_time

        if elapsed_time > 0:
            rate = self.message_count / elapsed_time
            bandwidth_bps = (self.bytes_received * 8) / elapsed_time # bits per second
            bandwidth_kBps = bandwidth_bps / (8 * 1024) # kilobytes per second

            self.get_logger().info(f"--- Topic: {self.topic_name} ({self.message_type_pkg}.msg.{self.message_type_name}) ---")
            self.get_logger().info(f"  Rate: {rate:.2f} msgs/sec")
            self.get_logger().info(f"  Bandwidth (approx): {bandwidth_kBps:.2f} kB/s")
            self.get_logger().info(f"  Total messages in last interval: {self.message_count}")

            if self.recent_messages_content:
                self.get_logger().info(f"  Recent messages (up to {self.max_messages_display}):")
                for i, content in enumerate(self.recent_messages_content):
                    self.get_logger().info(f"    Msg {i+1}: {content}")
            else:
                self.get_logger().info("  No messages received in the last interval.")
            self.get_logger().info("--------------------------------------------------")

        # Reset counters for the next interval
        self.message_count = 0
        self.bytes_received = 0
        self.last_display_time = current_time
        self.recent_messages_content = []

def main(args=None):
    rclpy.init(args=args)
    try:
        topic_monitor_node = TopicMonitorNode()
        rclpy.spin(topic_monitor_node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if 'topic_monitor_node' in locals():
            topic_monitor_node.get_logger().fatal(f"Unhandled exception: {e}", exc_info=True)
        else:
            print(f"Unhandled exception before node initialization: {e}")
    finally:
        if 'topic_monitor_node' in locals() and rclpy.ok():
            topic_monitor_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
