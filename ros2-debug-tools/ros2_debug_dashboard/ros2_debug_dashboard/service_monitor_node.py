import rclpy
from rclpy.node import Node
import importlib
import json # For parsing request_data string
import sys
import time

class ServiceMonitorNode(Node):
    def __init__(self):
        super().__init__('service_monitor_node')

        self.declare_parameter('action', 'list')  # 'list' or 'call'
        self.declare_parameter('service_name', '') # e.g., /add_two_ints
        self.declare_parameter('service_type_pkg', '') # e.g., example_interfaces
        self.declare_parameter('service_type_name', '') # e.g., AddTwoInts (from example_interfaces.srv)
        self.declare_parameter('request_data', '{}') # JSON string for request, e.g., '{"a": 1, "b": 2}'
        self.declare_parameter('timeout_sec', 5.0) # Timeout for service call

        self.action = self.get_parameter('action').get_parameter_value().string_value
        self.service_name_param = self.get_parameter('service_name').get_parameter_value().string_value
        self.service_type_pkg = self.get_parameter('service_type_pkg').get_parameter_value().string_value
        self.service_type_name = self.get_parameter('service_type_name').get_parameter_value().string_value
        self.request_data_str = self.get_parameter('request_data').get_parameter_value().string_value
        self.timeout_sec = self.get_parameter('timeout_sec').get_parameter_value().double_value

        if self.action == 'list':
            self.list_services()
            # Node should exit after listing. A more robust way is to use a timer to shutdown.
            self.get_logger().info("Service listing complete. Shutting down node.")
            # rclpy.shutdown() # This can be problematic if called directly in __init__
            self.create_timer(0.1, lambda: self.shutdown_node())

        elif self.action == 'call':
            if not self.service_name_param or not self.service_type_pkg or not self.service_type_name:
                self.get_logger().error("For 'call' action, 'service_name', 'service_type_pkg', and 'service_type_name' parameters are required.")
                self.create_timer(0.1, lambda: self.shutdown_node())
                return
            self.call_service()
            # Node should exit after calling.
            # self.create_timer(0.1, lambda: self.shutdown_node()) # call_service is async, shutdown there
        else:
            self.get_logger().error(f"Invalid action: {self.action}. Choose 'list' or 'call'.")
            self.create_timer(0.1, lambda: self.shutdown_node())

    def shutdown_node(self):
        self.get_logger().info("Shutting down ServiceMonitorNode.")
        self.destroy_node()
        # rclpy.shutdown() # Let the main function handle shutdown

    def list_services(self):
        self.get_logger().info("Discovering services...")
        # Wait a bit for discovery to populate
        # This is a bit of a hack; ROS2 discovery is asynchronous.
        # A better way might be to periodically check or use a discovery API if available.
        # For a simple CLI tool, a short wait is often acceptable.
        # time.sleep(1.0) # Giving some time for the node to discover services

        # The get_service_names_and_types method needs some time for the node to be fully operational
        # and discover services. Calling it immediately in __init__ might yield empty results.
        # A common pattern is to use a short timer if an action needs to be performed once after init.
        self.create_timer(0.5, self._do_list_services)

    def _do_list_services(self):
        # This timer callback will be destroyed after its first execution.
        if hasattr(self, '_list_services_timer'):
            self._list_services_timer.cancel()

        service_names_and_types = self.get_service_names_and_types()
        if not service_names_and_types:
            self.get_logger().info("No services discovered or node not fully initialized for discovery yet.")
            self.get_logger().info("If you just started the ROS graph, try again in a few seconds.")
        else:
            self.get_logger().info("Available Services:")
            for name, types in service_names_and_types:
                self.get_logger().info(f"  Name: {name}")
                for srv_type in types:
                    self.get_logger().info(f"    Type: {srv_type}")
                self.get_logger().info("  ---")

        # Since list_services was the goal, we can prepare to shut down.
        # self.shutdown_node() # Moved to __init__ timer for list action

    def call_service(self):
        self.get_logger().info(f"Attempting to call service: '{self.service_name_param}'")
        self.get_logger().info(f"Service type: '{self.service_type_pkg}.srv.{self.service_type_name}'")
        self.get_logger().info(f"Request data (JSON string): '{self.request_data_str}'")

        try:
            srv_module = importlib.import_module(f"{self.service_type_pkg}.srv")
            self.srv_type_class = getattr(srv_module, self.service_type_name)
        except ModuleNotFoundError:
            self.get_logger().error(f"Could not import service type module: {self.service_type_pkg}.srv")
            self.create_timer(0.1, lambda: self.shutdown_node())
            return
        except AttributeError:
            self.get_logger().error(f"Could not find service type '{self.service_type_name}' in module '{self.service_type_pkg}.srv'")
            self.create_timer(0.1, lambda: self.shutdown_node())
            return
        except Exception as e:
            self.get_logger().error(f"An unexpected error occurred during service type import: {e}")
            self.create_timer(0.1, lambda: self.shutdown_node())
            return

        client = self.create_client(self.srv_type_class, self.service_name_param)

        if not client.wait_for_service(timeout_sec=self.timeout_sec):
            self.get_logger().error(f"Service '{self.service_name_param}' not available after waiting {self.timeout_sec}s.")
            self.create_timer(0.1, lambda: self.shutdown_node())
            return

        self.get_logger().info(f"Service '{self.service_name_param}' is available.")

        request = self.srv_type_class.Request()
        try:
            request_dict = json.loads(self.request_data_str)
            for key, value in request_dict.items():
                if hasattr(request, key):
                    setattr(request, key, value)
                else:
                    self.get_logger().warning(f"Request object does not have attribute '{key}'. Ignoring.")
            self.get_logger().info(f"Parsed request: {request}")
        except json.JSONDecodeError:
            self.get_logger().error(f"Invalid JSON string for request_data: {self.request_data_str}")
            self.create_timer(0.1, lambda: self.shutdown_node())
            return
        except Exception as e:
            self.get_logger().error(f"Error setting request attributes: {e}")
            self.create_timer(0.1, lambda: self.shutdown_node())
            return

        self.future = client.call_async(request)
        self.future.add_done_callback(self.service_call_done_callback)
        self.get_logger().info("Service call initiated...")

    def service_call_done_callback(self, future):
        try:
            response = future.result()
            self.get_logger().info(f"Service call successful for '{self.service_name_param}'.")
            self.get_logger().info(f"Response:\n{response}")
        except Exception as e:
            self.get_logger().error(f"Service call failed for '{self.service_name_param}': {e!r}")
        finally:
            # Regardless of success or failure, prepare to shut down.
            self.create_timer(0.1, lambda: self.shutdown_node())


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ServiceMonitorNode()
        # If the action is 'list' or 'call', the node is designed to perform its task and then shutdown.
        # We need to spin to allow timers and async callbacks to execute.
        # The node's internal logic (timers calling shutdown_node) will handle exiting the spin.
        if node.action in ['list', 'call']:
             # If the node is already shutting down (e.g. bad params in init), spin might not be needed
            if rclpy.ok() and not node.is_destroyed(): # Check if node is still valid
                 # For list, a short spin might be enough for the timer to fire.
                 # For call, spin until the callback completes and calls shutdown.
                rclpy.spin(node) # Spin until node is destroyed or Ctrl-C
        else: # Should not happen if action validation is correct
            if node and rclpy.ok() and not node.is_destroyed():
                node.get_logger().info("Service monitor spinning (should self-terminate based on action).")
                rclpy.spin(node)

    except KeyboardInterrupt:
        if node:
            node.get_logger().info("KeyboardInterrupt, shutting down service monitor.")
    except Exception as e:
        if node:
            node.get_logger().fatal(f"Unhandled exception in ServiceMonitorNode: {e}", exc_info=True)
        else:
            print(f"Unhandled exception before ServiceMonitorNode initialization: {e}")
    finally:
        # Node should handle its own destruction through shutdown_node.
        # We just ensure rclpy shuts down if it's still ok.
        if rclpy.ok():
            # If node still exists and wasn't destroyed by its own logic (e.g. due to error before shutdown timer)
            if node and not node.is_destroyed():
                node.destroy_node()
            rclpy.shutdown()
        # print("Service Monitor main finished.")


if __name__ == '__main__':
    main()
