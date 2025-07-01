import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import Log
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

class LogMonitorNode(Node):
    def __init__(self):
        super().__init__('log_monitor_node')

        self.declare_parameter('log_level', 'INFO')  # DEBUG, INFO, WARN, ERROR, FATAL
        self.log_level_param = self.get_parameter('log_level').get_parameter_value().string_value.upper()

        # Mapping string levels to Log message constants
        self.level_map = {
            "DEBUG": Log.DEBUG,
            "INFO": Log.INFO,
            "WARN": Log.WARN,
            "ERROR": Log.ERROR,
            "FATAL": Log.FATAL,
        }

        self.min_log_level = self.level_map.get(self.log_level_param, Log.INFO)
        self.get_logger().info(f"Log monitor started. Minimum log level to display: {self.log_level_param} ({self.min_log_level})")

        # QoS for /rosout is typically ReliabilityPolicy.RELIABLE and DurabilityPolicy.VOLATILE
        # However, some systems might use TRANSIENT_LOCAL for /rosout to catch early messages.
        # Let's try to be robust, but typically /rosout is volatile.
        rosout_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE, # Or BEST_EFFORT if issues occur
            history=HistoryPolicy.KEEP_LAST,
            depth=100, # Keep a buffer of log messages
            durability=DurabilityPolicy.VOLATILE # Default for /rosout
        )

        self.subscription = self.create_subscription(
            Log,
            '/rosout',
            self.rosout_callback,
            rosout_qos  # Use specific QoS for /rosout
        )

        self.log_counts = {
            "DEBUG": 0, "INFO": 0, "WARN": 0, "ERROR": 0, "FATAL": 0, "UNKNOWN": 0
        }
        self.display_interval = 5.0 # seconds
        self.timer = self.create_timer(self.display_interval, self.display_summary)

    def get_level_str(self, level_int):
        for str_val, int_val in self.level_map.items():
            if int_val == level_int:
                return str_val
        return "UNKNOWN"

    def rosout_callback(self, msg: Log):
        log_level_str = self.get_level_str(msg.level)

        if msg.level >= self.min_log_level:
            # Format the timestamp (seconds and nanoseconds)
            timestamp_sec = msg.stamp.sec
            timestamp_nanosec = msg.stamp.nanosec

            self.get_logger().info(
                f"[{log_level_str}][{timestamp_sec}.{timestamp_nanosec:09d}] [{msg.name}]: {msg.msg} "
                f"(File: {msg.file}, Function: {msg.function}, Line: {msg.line})"
            )

        self.log_counts[log_level_str] = self.log_counts.get(log_level_str, 0) + 1

    def display_summary(self):
        summary_lines = ["--- Log Summary ---"]
        total_messages = 0
        for level, count in self.log_counts.items():
            if count > 0: # Only show levels with messages
                summary_lines.append(f"  {level}: {count} messages")
            total_messages +=count
        summary_lines.append(f"  Total messages processed in last interval: {total_messages}")
        summary_lines.append("-------------------")

        # Log the summary using the node's logger at INFO level
        # This avoids it being filtered by its own logic if min_log_level is high
        # However, if the logger itself is set to a higher severity, this might not show.
        # For a debug tool, printing directly is also an option.
        # For now, use self.get_logger().info for consistency.
        self.get_logger().info("\n".join(summary_lines))

        # Optionally reset counts per interval, or keep them cumulative
        # For now, let's keep them cumulative for the session
        # If resetting:
        # for key in self.log_counts: self.log_counts[key] = 0


def main(args=None):
    rclpy.init(args=args)
    log_monitor_node = None
    try:
        log_monitor_node = LogMonitorNode()
        rclpy.spin(log_monitor_node)
    except KeyboardInterrupt:
        if log_monitor_node:
            log_monitor_node.get_logger().info("KeyboardInterrupt, shutting down log monitor.")
    except Exception as e:
        if log_monitor_node:
            log_monitor_node.get_logger().fatal(f"Unhandled exception: {e}", exc_info=True)
        else:
            print(f"Unhandled exception before node initialization: {e}")
    finally:
        if log_monitor_node and rclpy.ok():
            # Display final summary before exiting
            log_monitor_node.display_summary()
            log_monitor_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
