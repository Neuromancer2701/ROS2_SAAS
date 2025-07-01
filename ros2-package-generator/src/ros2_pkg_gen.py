#!/usr/bin/env python3

import argparse
import os
import stat
from string import Template
import sys

# --- Template Definitions ---

# C++ CMakeLists.txt
CPP_CMAKELISTS_TEMPLATE = Template("""\
cmake_minimum_required(VERSION 3.8)
project(${package_name})

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
${dependencies}

add_executable(${node_name} src/${node_executable_name}.cpp)
ament_target_dependencies(${node_name} rclcpp ${link_libraries})
install(TARGETS ${node_name} DESTINATION lib/\${PROJECT_NAME})

${custom_interface_build_rules}

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
""")

# C++ package.xml
CPP_PACKAGE_XML_TEMPLATE = Template("""\
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>${package_name}</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="user@todo.todo">user</maintainer>
  <license>TODO: License declaration</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>rclcpp</depend>
${xml_dependencies}

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
""")

# Python setup.py
PY_SETUP_PY_TEMPLATE = Template("""\
from setuptools import find_packages, setup
import os
from glob import glob

package_name = '${package_name}'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))), # Example for launch files
        ${custom_interface_data_files}
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            '${node_name} = ${package_name}.${node_executable_name}:main'
        ],
    },
)
""")

# Python package.xml
PY_PACKAGE_XML_TEMPLATE = Template("""\
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>${package_name}</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="user@todo.todo">user</maintainer>
  <license>TODO: License declaration</license>

  <depend>rclpy</depend>
${xml_dependencies}

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
""")

# Python setup.cfg
PY_SETUP_CFG_TEMPLATE = """\
[develop]
script_dir=$base/lib/${package_name}
[install]
install_scripts=$base/lib/${package_name}
"""

# Python __init__.py (empty)
PY_INIT_PY_TEMPLATE = ""

# Python resource/<package_name> (empty marker file)
PY_RESOURCE_MARKER_TEMPLATE = ""

# Standard Python test files
PY_TEST_COPYRIGHT_TEMPLATE = Template("""\
# Copyright 2023 ${maintainer}
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_copyright.main import main
import pytest

def test_copyright():
    rc = main(argv=['.', 'test'])
    assert rc == 0, 'Found errors'
""")

PY_TEST_FLAKE8_TEMPLATE = Template("""\
# Copyright 2023 ${maintainer}
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_flake8.main import main_with_errors
import pytest

def test_flake8():
    rc, errors = main_with_errors(argv=['.'])
    assert rc == 0, 'Found %d code style errors / warnings:\n' % len(errors) + '\\n'.join(errors)
""")

PY_TEST_PEP257_TEMPLATE = Template("""\
# Copyright 2023 ${maintainer}
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_pep257.main import main
import pytest

def test_pep257():
    rc = main(argv=['.'])
    assert rc == 0, 'Found docstring style errors'
""")


# --- Node Specific Templates ---

# C++ Publisher
CPP_PUBLISHER_NODE_TEMPLATE = Template("""\
#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "${msg_include_path}" // e.g., "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class ${node_class_name} : public rclcpp::Node
{
public:
  ${node_class_name}()
  : Node("${node_name}"), count_(0)
  {
    publisher_ = this->create_publisher<${msg_type_colon}>("${topic_name}", 10);
    timer_ = this->create_wall_timer(
      500ms, std::bind(&${node_class_name}::timer_callback, this));
    RCLCPP_INFO(this->get_logger(), "Publisher node '${node_name}' started, publishing to '${topic_name}'.");
  }

private:
  void timer_callback()
  {
    auto message = ${msg_type_colon}();
    // Example: Populate message data. Adjust for your message type.
    // For std_msgs::msg::String:
    message.data = "Hello, world! " + std::to_string(count_++);
    // For other types, you'll need to set different fields.
    // e.g. for std_msgs::msg::Int32: message.data = count_++;

    RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str()); // Adjust for non-string msgs
    publisher_->publish(message);
  }
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<${msg_type_colon}>::SharedPtr publisher_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<${node_class_name}>());
  rclcpp::shutdown();
  return 0;
}
""")

# Python Publisher
PY_PUBLISHER_NODE_TEMPLATE = Template("""\
import rclpy
from rclpy.node import Node
from ${msg_module} import ${msg_class} # e.g., from std_msgs.msg import String
import time

class ${node_class_name}(Node):

    def __init__(self):
        super().__init__('${node_name}')
        self.publisher_ = self.create_publisher(${msg_class}, '${topic_name}', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        self.get_logger().info(f"Publisher node '${self.get_name()}' started, publishing to '${self.publisher_.topic_name}'.")

    def timer_callback(self):
        msg = ${msg_class}()
        # Example: Populate message data. Adjust for your message type.
        # For std_msgs.msg.String:
        msg.data = f'Hello World: {self.i}'
        # For other types, you'll need to set different fields.
        # e.g. for std_msgs.msg.Int32: msg.data = self.i

        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"') # Adjust for non-string msgs
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    node = ${node_class_name}()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
""")

# C++ Subscriber
CPP_SUBSCRIBER_NODE_TEMPLATE = Template("""\
#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "${msg_include_path}" // e.g., "std_msgs/msg/string.hpp"

using std::placeholders::_1;

class ${node_class_name} : public rclcpp::Node
{
public:
  ${node_class_name}()
  : Node("${node_name}")
  {
    subscription_ = this->create_subscription<${msg_type_colon}>(
      "${topic_name}", 10, std::bind(&${node_class_name}::topic_callback, this, _1));
    RCLCPP_INFO(this->get_logger(), "Subscriber node '${node_name}' started, listening to '${topic_name}'.");
  }

private:
  void topic_callback(const ${msg_type_colon}::SharedPtr msg) const
  {
    // Example: Process message data. Adjust for your message type.
    // For std_msgs::msg::String:
    RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
    // For other types, you'll need to access different fields.
    // e.g. for std_msgs::msg::Int32: RCLCPP_INFO(this->get_logger(), "I heard: '%d'", msg->data);
  }
  rclcpp::Subscription<${msg_type_colon}>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<${node_class_name}>());
  rclcpp::shutdown();
  return 0;
}
""")

# Python Subscriber
PY_SUBSCRIBER_NODE_TEMPLATE = Template("""\
import rclpy
from rclpy.node import Node
from ${msg_module} import ${msg_class} # e.g., from std_msgs.msg import String

class ${node_class_name}(Node):

    def __init__(self):
        super().__init__('${node_name}')
        self.subscription = self.create_subscription(
            ${msg_class},
            '${topic_name}',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.get_logger().info(f"Subscriber node '${self.get_name()}' started, listening to '${self.subscription.topic_name}'.")

    def listener_callback(self, msg):
        # Example: Process message data. Adjust for your message type.
        # For std_msgs.msg.String:
        self.get_logger().info(f'I heard: "{msg.data}"')
        # For other types, you'll need to access different fields.
        # e.g. for std_msgs.msg.Int32: self.get_logger().info(f'I heard: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    node = ${node_class_name}()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
""")

# C++ Service Server
CPP_SERVICE_SERVER_NODE_TEMPLATE = Template("""\
#include "rclcpp/rclcpp.hpp"
#include "${srv_include_path}" // e.g., "example_interfaces/srv/add_two_ints.hpp"
#include <memory>

void handle_service(
  const std::shared_ptr<${srv_type_colon}::Request> request,
  std::shared_ptr<${srv_type_colon}::Response> response)
{
  // Example: Process request and populate response. Adjust for your service type.
  // For example_interfaces::srv::AddTwoInts:
  // response->sum = request->a + request->b;
  // RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Incoming request\\na: %ld" " b: %ld", request->a, request->b);
  // RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "sending back response: [%ld]", (long int)response->sum);

  // For custom service (e.g., CustomSrv with request_data and response_data fields):
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Incoming request data: '%s'", request->request_data.c_str());
  response->response_data = "Response to: " + request->request_data;
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Sending back response: '%s'", response->response_data.c_str());
}

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("${node_name}");

  rclcpp::Service<${srv_type_colon}>::SharedPtr service =
    node->create_service<${srv_type_colon}>("${service_name}", &handle_service);

  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service server '${service_name}' ready.");

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
""")

# Python Service Server
PY_SERVICE_SERVER_NODE_TEMPLATE = Template("""\
from ${srv_module} import ${srv_class} # e.g., from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node

class ${node_class_name}(Node):

    def __init__(self):
        super().__init__('${node_name}')
        self.srv = self.create_service(${srv_class}, '${service_name}', self.service_callback)
        self.get_logger().info(f"Service server '${self.srv.srv_name}' ready.")

    def service_callback(self, request, response):
        # Example: Process request and populate response. Adjust for your service type.
        # For example_interfaces.srv.AddTwoInts:
        # response.sum = request.a + request.b
        # self.get_logger().info(f'Incoming request\\na: {request.a} b: {request.b}')
        # self.get_logger().info(f'Sending back response: {response.sum}')

        # For custom service (e.g., CustomSrv with request_data and response_data fields):
        self.get_logger().info(f'Incoming request data: "{request.request_data}"')
        response.response_data = f"Response to: {request.request_data}"
        self.get_logger().info(f'Sending back response: "{response.response_data}"')
        return response

def main(args=None):
    rclpy.init(args=args)
    node = ${node_class_name}()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
""")

# C++ Service Client
CPP_SERVICE_CLIENT_NODE_TEMPLATE = Template("""\
#include "rclcpp/rclcpp.hpp"
#include "${srv_include_path}" // e.g., "example_interfaces/srv/add_two_ints.hpp"
#include <chrono>
#include <cstdlib>
#include <memory>

using namespace std::chrono_literals;

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  // Example: Basic argument parsing. Adjust for your service type's request fields.
  // if (argc != 3) { // For AddTwoInts
  //     RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "usage: ${node_name} X Y");
  //     return 1;
  // }
  if (argc != 2) { // For CustomSrv with one string request
      RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "usage: ${node_name} <string_data>");
      return 1;
  }


  std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("${node_name}_client");
  rclcpp::Client<${srv_type_colon}>::SharedPtr client =
    node->create_client<${srv_type_colon}>("${service_name}");

  auto request = std::make_shared<${srv_type_colon}::Request>();
  // Example: Populate request. Adjust for your service type.
  // For AddTwoInts:
  // request->a = atoll(argv[1]);
  // request->b = atoll(argv[2]);
  // For CustomSrv:
  request->request_data = argv[1];


  while (!client->wait_for_service(1s)) {
    if (!rclcpp::ok()) {
      RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Interrupted while waiting for the service. Exiting.");
      return 0;
    }
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service '${service_name}' not available, waiting again...");
  }

  auto result_future = client->async_send_request(request);
  // Wait for the result.
  if (rclcpp::spin_until_future_complete(node, result_future) ==
    rclcpp::FutureReturnCode::SUCCESS)
  {
    auto result = result_future.get();
    // Example: Process response. Adjust for your service type.
    // For AddTwoInts:
    // RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Sum: %ld", result->sum);
    // For CustomSrv:
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Response: %s", result->response_data.c_str());
  } else {
    RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Failed to call service ${service_name}");
  }

  rclcpp::shutdown();
  return 0;
}
""")

# Python Service Client
PY_SERVICE_CLIENT_NODE_TEMPLATE = Template("""\
from ${srv_module} import ${srv_class} # e.g., from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node
import sys

class ${node_class_name}(Node):

    def __init__(self):
        super().__init__('${node_name}_client')
        self.cli = self.create_client(${srv_class}, '${service_name}')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Service '${service_name}' not available, waiting again...")
        self.req = ${srv_class}.Request()

    def send_request(self, args): # Changed to accept generic args
        # Example: Populate request. Adjust for your service type.
        # For AddTwoInts:
        # self.req.a = int(args[0])
        # self.req.b = int(args[1])
        # For CustomSrv:
        self.req.request_data = str(args[0])

        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    rclpy.init(args=args)
    client_node = ${node_class_name}()

    # Example: Basic argument handling. Adjust for your service type's request fields.
    # if len(sys.argv) != 3: # For AddTwoInts
    #     client_node.get_logger().info('Usage: ${node_name}_client X Y')
    #     sys.exit(1)
    if len(sys.argv) != 2: # For CustomSrv
        client_node.get_logger().info('Usage: ${node_name}_client <string_data>')
        sys.exit(1)

    # Pass relevant arguments to send_request
    response = client_node.send_request(sys.argv[1:]) # Pass all args after script name

    if response:
        # Example: Process response. Adjust for your service type.
        # For AddTwoInts:
        # client_node.get_logger().info(f'Sum: {response.sum}')
        # For CustomSrv:
        client_node.get_logger().info(f'Response: {response.response_data}')
    else:
        client_node.get_logger().error('Exception while calling service')

    client_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
""")


# C++ Action Server
CPP_ACTION_SERVER_NODE_TEMPLATE = Template("""\
#include <functional>
#include <memory>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "${action_include_path}" // e.g., "action_tutorials_interfaces/action/fibonacci.hpp"

class ${node_class_name} : public rclcpp::Node
{
public:
  using ${action_name_pascal} = ${action_type_colon};
  using GoalHandle${action_name_pascal} = rclcpp_action::ServerGoalHandle<${action_name_pascal}>;

  explicit ${node_class_name}(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("${node_name}", options)
  {
    using namespace std::placeholders;

    this->action_server_ = rclcpp_action::create_server<${action_name_pascal}>(
      this,
      "${action_name}",
      std::bind(&${node_class_name}::handle_goal, this, _1, _2),
      std::bind(&${node_class_name}::handle_cancel, this, _1),
      std::bind(&${node_class_name}::handle_accepted, this, _1));
    RCLCPP_INFO(this->get_logger(), "Action server '${action_name}' ready.");
  }

private:
  rclcpp_action::Server<${action_name_pascal}>::SharedPtr action_server_;

  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID & /*uuid*/,
    std::shared_ptr<const ${action_name_pascal}::Goal> goal)
  {
    // Example: Validate goal. Adjust for your action type.
    // For Fibonacci:
    // RCLCPP_INFO(this->get_logger(), "Received goal request with order %d", goal->order);
    // if (goal->order > 20) { // Max order for this example
    //   RCLCPP_WARN(this->get_logger(), "Goal order too high, rejecting.");
    //   return rclcpp_action::GoalResponse::REJECT;
    // }
    // For CustomAction (e.g., goal->goal_data):
    RCLCPP_INFO(this->get_logger(), "Received goal request with data: %s", goal->goal_data.c_str());
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandle${action_name_pascal}> /*goal_handle*/)
  {
    RCLCPP_INFO(this->get_logger(), "Received request to cancel goal");
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandle${action_name_pascal}> goal_handle)
  {
    using namespace std::placeholders;
    // this needs to return quickly to avoid blocking the executor, so spin up a new thread
    std::thread{std::bind(&${node_class_name}::execute, this, _1), goal_handle}.detach();
  }

  void execute(const std::shared_ptr<GoalHandle${action_name_pascal}> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Executing goal");
    rclcpp::Rate loop_rate(1); // 1 Hz for feedback
    const auto goal = goal_handle->get_goal();
    auto feedback = std::make_shared<${action_name_pascal}::Feedback>();
    auto result = std::make_shared<${action_name_pascal}::Result>();

    // Example: Action execution logic. Adjust for your action type.
    // For Fibonacci:
    // auto & sequence = feedback->partial_sequence;
    // sequence.push_back(0);
    // sequence.push_back(1);
    // for (int i = 1; (i < goal->order) && rclcpp::ok(); ++i) {
    //   if (goal_handle->is_canceling()) {
    //     result->sequence = sequence;
    //     goal_handle->canceled(result);
    //     RCLCPP_INFO(this->get_logger(), "Goal canceled");
    //     return;
    //   }
    //   sequence.push_back(sequence[i] + sequence[i - 1]);
    //   goal_handle->publish_feedback(feedback);
    //   RCLCPP_INFO(this->get_logger(), "Publishing feedback");
    //   loop_rate.sleep();
    // }
    // result->sequence = sequence;

    // For CustomAction (e.g., goal->goal_data, feedback->feedback_message, result->result_status):
    std::string current_status = "Processing: " + goal->goal_data;
    for (int i = 0; i < 5 && rclcpp::ok(); ++i) {
        if (goal_handle->is_canceling()) {
            result->result_status = "Goal Canceled during processing " + goal->goal_data;
            goal_handle->canceled(result);
            RCLCPP_INFO(this->get_logger(), "Goal Canceled");
            return;
        }
        current_status += ".";
        feedback->feedback_message = current_status + " (" + std::to_string(i+1) + "/5)";
        goal_handle->publish_feedback(feedback);
        RCLCPP_INFO(this->get_logger(), "Publishing feedback: %s", feedback->feedback_message.c_str());
        loop_rate.sleep();
    }
    result->result_status = "Successfully processed: " + goal->goal_data;


    if (rclcpp::ok()) {
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(), "Goal succeeded");
    }
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto action_server_node = std::make_shared<${node_class_name}>();
  rclcpp::spin(action_server_node);
  rclcpp::shutdown();
  return 0;
}
""")

# Python Action Server
PY_ACTION_SERVER_NODE_TEMPLATE = Template("""\
import time
import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node
from ${action_module} import ${action_class} # e.g., from action_tutorials_interfaces.action import Fibonacci

class ${node_class_name}(Node):

    def __init__(self):
        super().__init__('${node_name}')
        self._action_server = ActionServer(
            self,
            ${action_class},
            '${action_name}',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            handle_accepted_callback=self.handle_accepted_callback,
            cancel_callback=self.cancel_callback
        )
        self.get_logger().info(f"Action server '${self._action_server.action_name}' ready.")

    def goal_callback(self, goal_request):
        # Example: Validate goal. Adjust for your action type.
        # For Fibonacci:
        # self.get_logger().info(f'Received goal request with order {goal_request.order}')
        # if goal_request.order > 20: # Max order for this example
        #    self.get_logger().warn('Goal order too high, rejecting.')
        #    return GoalResponse.REJECT
        # For CustomAction (e.g., goal_request.goal_data):
        self.get_logger().info(f'Received goal request with data: "{goal_request.goal_data}"')
        return GoalResponse.ACCEPT

    def handle_accepted_callback(self, goal_handle):
        self.get_logger().info('Goal accepted, executing...')
        goal_handle.execute() # This will call execute_callback in a new thread

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received request to cancel goal')
        return CancelResponse.ACCEPT # Accept the cancellation

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')
        feedback_msg = ${action_class}.Feedback()
        result = ${action_class}.Result()

        # Example: Action execution logic. Adjust for your action type.
        # For Fibonacci:
        # sequence = [0, 1]
        # feedback_msg.partial_sequence = sequence
        # for i in range(1, goal_handle.request.order):
        #     if not goal_handle.is_active:
        #         self.get_logger().info('Goal aborted')
        #         return ${action_class}.Result() # Empty result if aborted
        #     if goal_handle.is_cancel_requested:
        #         goal_handle.canceled()
        #         self.get_logger().info('Goal canceled')
        #         result.sequence = sequence
        #         return result
        #
        #     sequence.append(sequence[i] + sequence[i-1])
        #     feedback_msg.partial_sequence = sequence
        #     self.get_logger().info(f'Publishing feedback: {feedback_msg.partial_sequence}')
        #     goal_handle.publish_feedback(feedback_msg)
        #     time.sleep(1)
        #
        # goal_handle.succeed()
        # result.sequence = sequence

        # For CustomAction (e.g., goal_handle.request.goal_data, feedback_msg.feedback_message, result.result_status):
        current_status = f"Processing: {goal_handle.request.goal_data}"
        for i in range(5):
            if not goal_handle.is_active:
                self.get_logger().info('Goal aborted')
                return ${action_class}.Result() # Empty result if aborted
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.result_status = f"Goal Canceled during processing {goal_handle.request.goal_data}"
                self.get_logger().info('Goal Canceled')
                return result

            current_status += "."
            feedback_msg.feedback_message = f"{current_status} ({i+1}/5)"
            self.get_logger().info(f'Publishing feedback: {feedback_msg.feedback_message}')
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1)

        goal_handle.succeed()
        result.result_status = f"Successfully processed: {goal_handle.request.goal_data}"

        self.get_logger().info(f'Returning result: {result.result_status if hasattr(result, "result_status") else "N/A"}')
        return result

def main(args=None):
    rclpy.init(args=args)
    action_server_node = ${node_class_name}()
    try:
        rclpy.spin(action_server_node)
    except KeyboardInterrupt:
        pass
    finally:
        action_server_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
""")

# C++ Action Client
CPP_ACTION_CLIENT_NODE_TEMPLATE = Template("""\
#include <functional>
#include <future>
#include <memory>
#include <string>
#include <sstream>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "${action_include_path}" // e.g., "action_tutorials_interfaces/action/fibonacci.hpp"

class ${node_class_name} : public rclcpp::Node
{
public:
  using ${action_name_pascal} = ${action_type_colon};
  using GoalHandle${action_name_pascal} = rclcpp_action::ClientGoalHandle<${action_name_pascal}>;

  explicit ${node_class_name}(const rclcpp::NodeOptions & node_options = rclcpp::NodeOptions())
  : Node("${node_name}_client", node_options)
  {
    this->client_ptr_ = rclcpp_action::create_client<${action_name_pascal}>(
      this,
      "${action_name}");
  }

  void send_goal(const typename ${action_name_pascal}::Goal &goal_msg)
  {
    using namespace std::placeholders;

    if (!this->client_ptr_->wait_for_action_server(std::chrono::seconds(10))) {
      RCLCPP_ERROR(this->get_logger(), "Action server '${action_name}' not available after waiting");
      rclcpp::shutdown();
      return;
    }

    RCLCPP_INFO(this->get_logger(), "Sending goal");

    auto send_goal_options = rclcpp_action::Client<${action_name_pascal}>::SendGoalOptions();
    send_goal_options.goal_response_callback =
      std::bind(&${node_class_name}::goal_response_callback, this, _1);
    send_goal_options.feedback_callback =
      std::bind(&${node_class_name}::feedback_callback, this, _1, _2);
    send_goal_options.result_callback =
      std::bind(&${node_class_name}::result_callback, this, _1);

    this->client_ptr_->async_send_goal(goal_msg, send_goal_options);
  }

private:
  rclcpp_action::Client<${action_name_pascal}>::SharedPtr client_ptr_;
  rclcpp::TimerBase::SharedPtr timer_; // Example for periodic goal sending or timeout

  void goal_response_callback(const GoalHandle${action_name_pascal}::SharedPtr & goal_handle)
  {
    if (!goal_handle) {
      RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
    } else {
      RCLCPP_INFO(this->get_logger(), "Goal accepted by server, waiting for result");
    }
  }

  void feedback_callback(
    GoalHandle${action_name_pascal}::SharedPtr,
    const std::shared_ptr<const ${action_name_pascal}::Feedback> feedback)
  {
    // Example: Process feedback. Adjust for your action type.
    // For Fibonacci:
    // std::stringstream ss;
    // ss << "Next number in sequence received: ";
    // for (auto number : feedback->partial_sequence) {
    //   ss << number << " ";
    // }
    // RCLCPP_INFO(this->get_logger(), ss.str().c_str());
    // For CustomAction (e.g. feedback->feedback_message):
    RCLCPP_INFO(this->get_logger(), "Feedback received: %s", feedback->feedback_message.c_str());
  }

  void result_callback(const GoalHandle${action_name_pascal}::WrappedResult & result)
  {
    switch (result.code) {
      case rclcpp_action::ResultCode::SUCCEEDED:
        // Example: Process result. Adjust for your action type.
        // For Fibonacci:
        // {
        //   std::stringstream ss;
        //   ss << "Result received: ";
        //   for (auto number : result.result->sequence) {
        //     ss << number << " ";
        //   }
        //   RCLCPP_INFO(this->get_logger(), ss.str().c_str());
        // }
        // For CustomAction (e.g. result.result->result_status):
        RCLCPP_INFO(this->get_logger(), "Result received: %s", result.result->result_status.c_str());
        break;
      case rclcpp_action::ResultCode::ABORTED:
        RCLCPP_ERROR(this->get_logger(), "Goal was aborted");
        break;
      case rclcpp_action::ResultCode::CANCELED:
        RCLCPP_ERROR(this->get_logger(), "Goal was canceled");
        break;
      default:
        RCLCPP_ERROR(this->get_logger(), "Unknown result code");
        break;
    }
    rclcpp::shutdown(); // Or handle completion differently
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto action_client_node = std::make_shared<${node_class_name}>();

  // Example: Create and send goal. Adjust for your action type's goal fields.
  typename ${node_class_name}::${action_name_pascal}::Goal goal_msg;
  // For Fibonacci:
  // if (argc < 2) {
  //   RCLCPP_ERROR(action_client_node->get_logger(), "Usage: ${node_name}_client <order>");
  //   rclcpp::shutdown();
  //   return 1;
  // }
  // goal_msg.order = atoi(argv[1]);
  // For CustomAction (e.g. goal_msg.goal_data):
  if (argc < 2) {
    RCLCPP_ERROR(action_client_node->get_logger(), "Usage: ${node_name}_client <goal_data_string>");
    rclcpp::shutdown();
    return 1;
  }
  goal_msg.goal_data = argv[1];

  action_client_node->send_goal(goal_msg);
  rclcpp::spin(action_client_node);
  // rclcpp::shutdown(); // Shutdown is handled in result_callback or if server not found
  return 0;
}
""")

# Python Action Client
PY_ACTION_CLIENT_NODE_TEMPLATE = Template("""\
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from ${action_module} import ${action_class} # e.g., from action_tutorials_interfaces.action import Fibonacci
import sys

class ${node_class_name}(Node):

    def __init__(self):
        super().__init__('${node_name}_client')
        self._action_client = ActionClient(self, ${action_class}, '${action_name}')

    def send_goal(self, goal_msg_args): # Changed to accept generic args for goal
        goal_msg = ${action_class}.Goal()
        # Example: Populate goal. Adjust for your action type.
        # For Fibonacci:
        # goal_msg.order = int(goal_msg_args[0])
        # For CustomAction (e.g. goal_msg.goal_data):
        goal_msg.goal_data = str(goal_msg_args[0])


        self.get_logger().info("Waiting for action server '${action_name}'...")
        self._action_client.wait_for_server()

        self.get_logger().info(f'Sending goal request...') # Adjust log for goal content
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            rclpy.shutdown() # Added shutdown
            return

        self.get_logger().info('Goal accepted :)')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        # Example: Process result. Adjust for your action type.
        # For Fibonacci:
        # self.get_logger().info(f'Result: {result.sequence}')
        # For CustomAction (e.g. result.result_status):
        self.get_logger().info(f'Result: {result.result_status}')
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        # Example: Process feedback. Adjust for your action type.
        # For Fibonacci:
        # self.get_logger().info(f'Received feedback: {feedback.partial_sequence}')
        # For CustomAction (e.g. feedback.feedback_message):
        self.get_logger().info(f'Received feedback: {feedback.feedback_message}')


def main(args=None):
    rclpy.init(args=args)
    action_client_node = ${node_class_name}()

    # Example: Basic argument handling. Adjust for your action type's goal fields.
    # if len(sys.argv) < 2: # For Fibonacci
    #     action_client_node.get_logger().error('Usage: ${node_name}_client <order>')
    #     sys.exit(1)
    # goal_args = sys.argv[1:]
    if len(sys.argv) < 2: # For CustomAction
        action_client_node.get_logger().error('Usage: ${node_name}_client <goal_data_string>')
        sys.exit(1)
    goal_args = sys.argv[1:]


    action_client_node.send_goal(goal_args) # Pass relevant args
    try:
        rclpy.spin(action_client_node)
    except KeyboardInterrupt:
        action_client_node.get_logger().info('User interrupted, shutting down.')
    finally:
        if rclpy.ok(): # Check if not already shut down by result callback
            action_client_node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
""")


# Custom .srv file template
CUSTOM_SRV_TEMPLATE = Template("""\
# Request
string request_data
---
# Response
string response_data
""")

# Custom .action file template
CUSTOM_ACTION_TEMPLATE = Template("""\
# Goal
string goal_data
---
# Result
string result_status
---
# Feedback
string feedback_message
""")


# --- Helper Functions ---

def to_pascal_case(text):
    return "".join(word.capitalize() for word in text.split('_'))

def make_executable(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def parse_ros_type(ros_type_str):
    """ Parses a ROS type string like 'std_msgs/msg/String' into package, type_folder, name """
    parts = ros_type_str.split('/')
    if len(parts) == 3: # e.g. std_msgs/msg/String
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2: # e.g. my_interfaces/CustomSrv (assuming srv or action)
        # This case is ambiguous without knowing if it's msg, srv, or action.
        # The caller should handle this distinction.
        # For custom types generated within the package, this will be <package_name>/<type_name>
        return parts[0], None, parts[1] # type_folder is None
    raise ValueError(f"Invalid ROS type string: {ros_type_str}")


def get_type_details(ros_type_str, type_category, package_name, is_custom_generated=False):
    """
    Generates include paths, C++ types, Python modules/classes for msg, srv, action.
    type_category: 'msg', 'srv', 'action'
    is_custom_generated: True if the .srv or .action file is being generated in this package.
    """
    pkg, type_folder, name = parse_ros_type(ros_type_str)

    if is_custom_generated:
        # For types defined within the current package (e.g. srv/CustomSrv.srv)
        # The include path for C++ will be <package_name>/<type_category>/<name>.hpp
        # The Python module will be <package_name>.<type_category>
        cpp_include_path = f"{package_name}/{type_category}/{name}.hpp"
        cpp_type_colon = f"{package_name}::{type_category}::{name}"
        py_module = f"{package_name}.{type_category}"
        py_class = name
    else:
        # For standard or external types (e.g. std_msgs/msg/String)
        cpp_include_path = f"{pkg}/{type_folder}/{name}.hpp"
        cpp_type_colon = f"{pkg}::{type_folder}::{name}"
        py_module = f"{pkg}.{type_folder}"
        py_class = name

    return cpp_include_path, cpp_type_colon, py_module, py_class


def create_package_files(args):
    package_path = os.path.join(args.target_path, args.package_name)
    if os.path.exists(package_path):
        print(f"Error: Directory '{package_path}' already exists. Please choose a different name or path.")
        sys.exit(1)

    os.makedirs(package_path, exist_ok=True)
    print(f"Creating package '{args.package_name}' at '{package_path}'")

    node_name_safe = args.node_name.replace('-', '_') # Ensure node name is valid for filenames/classnames
    node_class_name = to_pascal_case(node_name_safe)
    node_executable_name = node_name_safe # For C++ .cpp file and Python .py file

    # --- Interface handling (msg, srv, action) ---
    is_custom_srv = False
    is_custom_action = False
    custom_interface_build_rules_cpp = ""
    custom_interface_data_files_py = ""
    xml_dependencies_list = [] # For package.xml
    cmake_dependencies_list = [] # For CMakeLists.txt
    cmake_link_libraries_list = [] # For CMakeLists.txt target_link_libraries

    # Message type
    if args.node_type in ['publisher', 'subscriber']:
        msg_pkg, _, msg_name_only = parse_ros_type(args.msg_type)
        msg_include_path, msg_type_colon, msg_module, msg_class = get_type_details(args.msg_type, 'msg', args.package_name)
        if msg_pkg != args.package_name: # External message package
            xml_dependencies_list.append(f"  <depend>{msg_pkg}</depend>")
            cmake_dependencies_list.append(f"find_package({msg_pkg} REQUIRED)")
            cmake_link_libraries_list.append(msg_pkg)
        # For messages, we assume they are not generated by this script directly, so no custom build rules needed here
        # unless it's a message from a sub-package, which is not handled by this basic generator.

    # Service type
    if args.node_type in ['service_server', 'service_client']:
        if "/" not in args.srv_type: # Custom service type, e.g., "MySrv"
            is_custom_srv = True
            srv_name_only = args.srv_type
            args.srv_type = f"{args.package_name}/srv/{srv_name_only}" # Full path for internal use
            srv_pkg, _, _ = parse_ros_type(args.srv_type) # srv_pkg will be args.package_name
        else:
            srv_pkg, _, srv_name_only = parse_ros_type(args.srv_type)

        srv_include_path, srv_type_colon, srv_module, srv_class = get_type_details(
            args.srv_type, 'srv', args.package_name, is_custom_srv
        )

        if is_custom_srv:
            os.makedirs(os.path.join(package_path, "srv"), exist_ok=True)
            with open(os.path.join(package_path, "srv", f"{srv_name_only}.srv"), 'w') as f:
                f.write(CUSTOM_SRV_TEMPLATE.substitute())
            print(f"  Created custom service definition: srv/{srv_name_only}.srv")

            xml_dependencies_list.append("  <build_depend>rosidl_default_generators</build_depend>")
            xml_dependencies_list.append("  <exec_depend>rosidl_default_runtime</exec_depend>")
            xml_dependencies_list.append("  <member_of_group>rosidl_interface_packages</member_of_group>")

            custom_interface_build_rules_cpp = f"""
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${{PROJECT_NAME}}
  "srv/{srv_name_only}.srv"
)"""
            custom_interface_data_files_py = f"""(os.path.join('share', package_name, 'srv'), glob(os.path.join('srv', '*.srv'))),"""
            cmake_dependencies_list.append(f"find_package(rosidl_default_generators REQUIRED)") # Already added by rule
            cmake_link_libraries_list.append(f"${{{args.package_name}_uninstall_target}}") # for C++
        elif srv_pkg != args.package_name:
            xml_dependencies_list.append(f"  <depend>{srv_pkg}</depend>")
            cmake_dependencies_list.append(f"find_package({srv_pkg} REQUIRED)")
            cmake_link_libraries_list.append(srv_pkg)


    # Action type
    if args.node_type in ['action_server', 'action_client']:
        action_name_pascal = to_pascal_case(args.action_name) # For C++ class usage
        if "/" not in args.action_type: # Custom action type
            is_custom_action = True
            action_name_only = args.action_type
            args.action_type = f"{args.package_name}/action/{action_name_only}"
            action_pkg, _, _ = parse_ros_type(args.action_type)
        else:
            action_pkg, _, action_name_only = parse_ros_type(args.action_type)

        action_include_path, action_type_colon, action_module, action_class = get_type_details(
            args.action_type, 'action', args.package_name, is_custom_action
        )

        if is_custom_action:
            os.makedirs(os.path.join(package_path, "action"), exist_ok=True)
            with open(os.path.join(package_path, "action", f"{action_name_only}.action"), 'w') as f:
                f.write(CUSTOM_ACTION_TEMPLATE.substitute())
            print(f"  Created custom action definition: action/{action_name_only}.action")

            xml_dependencies_list.append("  <build_depend>rosidl_default_generators</build_depend>")
            xml_dependencies_list.append("  <depend>action_msgs</depend>") # Action clients/servers depend on action_msgs
            xml_dependencies_list.append("  <exec_depend>rosidl_default_runtime</exec_depend>")
            xml_dependencies_list.append("  <member_of_group>rosidl_interface_packages</member_of_group>")

            # Add to existing rules if srv also custom
            custom_interface_build_rules_cpp += f"""
rosidl_generate_interfaces(${{PROJECT_NAME}}
  "action/{action_name_only}.action"
  DEPENDENCIES action_msgs # Required for actions
)""" if not custom_interface_build_rules_cpp else f"""
  "action/{action_name_only}.action"
  DEPENDENCIES action_msgs""" # Append to existing rosidl_generate_interfaces call

            if not custom_interface_build_rules_cpp.startswith("find_package(rosidl_default_generators REQUIRED)"):
                 custom_interface_build_rules_cpp = f"find_package(rosidl_default_generators REQUIRED)\n" + custom_interface_build_rules_cpp.strip()


            custom_interface_data_files_py += f"""\n        (os.path.join('share', package_name, 'action'), glob(os.path.join('action', '*.action'))),"""
            if "find_package(rosidl_default_generators REQUIRED)" not in cmake_dependencies_list:
                 cmake_dependencies_list.append(f"find_package(rosidl_default_generators REQUIRED)")
            if f"${{{args.package_name}_uninstall_target}}" not in cmake_link_libraries_list: # for C++
                 cmake_link_libraries_list.append(f"${{{args.package_name}_uninstall_target}}")
            if "action_msgs" not in xml_dependencies_list: # Ensure action_msgs is a general dependency
                xml_dependencies_list.append("  <depend>action_msgs</depend>")
            if "find_package(action_msgs REQUIRED)" not in cmake_dependencies_list:
                cmake_dependencies_list.append("find_package(action_msgs REQUIRED)")
            if "action_msgs" not in cmake_link_libraries_list:
                cmake_link_libraries_list.append("action_msgs")


        elif action_pkg != args.package_name:
            xml_dependencies_list.append(f"  <depend>{action_pkg}</depend>")
            xml_dependencies_list.append(f"  <depend>action_msgs</depend>") # External actions also need action_msgs
            cmake_dependencies_list.append(f"find_package({action_pkg} REQUIRED)")
            cmake_dependencies_list.append(f"find_package(action_msgs REQUIRED)")
            cmake_link_libraries_list.append(action_pkg)
            cmake_link_libraries_list.append("action_msgs")


    # Consolidate dependencies
    xml_dependencies = "\n".join(sorted(list(set(xml_dependencies_list))))
    cmake_dependencies = "\n".join(sorted(list(set(cmake_dependencies_list))))
    cmake_link_libraries = " ".join(sorted(list(set(cmake_link_libraries_list))))


    # --- Language specific file generation ---
    if args.language == 'cpp':
        # Create src and include directories
        os.makedirs(os.path.join(package_path, "src"), exist_ok=True)
        os.makedirs(os.path.join(package_path, "include", args.package_name), exist_ok=True)

        # CMakeLists.txt
        cmakelists_content = CPP_CMAKELISTS_TEMPLATE.substitute(
            package_name=args.package_name,
            node_name=node_name_safe, # Executable name
            node_executable_name=node_executable_name, # Source file name without .cpp
            dependencies=cmake_dependencies,
            link_libraries=cmake_link_libraries,
            custom_interface_build_rules=custom_interface_build_rules_cpp
        )
        with open(os.path.join(package_path, "CMakeLists.txt"), 'w') as f:
            f.write(cmakelists_content)
        print("  Created CMakeLists.txt")

        # package.xml
        package_xml_content = CPP_PACKAGE_XML_TEMPLATE.substitute(
            package_name=args.package_name,
            xml_dependencies=xml_dependencies
        )
        with open(os.path.join(package_path, "package.xml"), 'w') as f:
            f.write(package_xml_content)
        print("  Created package.xml")

        # Node source file
        node_template = None
        template_vars = {
            'node_name': node_name_safe,
            'node_class_name': node_class_name,
            'package_name': args.package_name,
        }
        if args.node_type == 'publisher':
            node_template = CPP_PUBLISHER_NODE_TEMPLATE
            template_vars.update({
                'topic_name': args.topic_name,
                'msg_type_colon': msg_type_colon,
                'msg_include_path': msg_include_path,
            })
        elif args.node_type == 'subscriber':
            node_template = CPP_SUBSCRIBER_NODE_TEMPLATE
            template_vars.update({
                'topic_name': args.topic_name,
                'msg_type_colon': msg_type_colon,
                'msg_include_path': msg_include_path,
            })
        elif args.node_type == 'service_server':
            node_template = CPP_SERVICE_SERVER_NODE_TEMPLATE
            template_vars.update({
                'service_name': args.service_name,
                'srv_type_colon': srv_type_colon,
                'srv_include_path': srv_include_path,
            })
        elif args.node_type == 'service_client':
            node_template = CPP_SERVICE_CLIENT_NODE_TEMPLATE
            template_vars.update({
                'service_name': args.service_name,
                'srv_type_colon': srv_type_colon,
                'srv_include_path': srv_include_path,
            })
        elif args.node_type == 'action_server':
            node_template = CPP_ACTION_SERVER_NODE_TEMPLATE
            template_vars.update({
                'action_name': args.action_name,
                'action_name_pascal': action_name_pascal,
                'action_type_colon': action_type_colon,
                'action_include_path': action_include_path,
            })
        elif args.node_type == 'action_client':
            node_template = CPP_ACTION_CLIENT_NODE_TEMPLATE
            template_vars.update({
                'action_name': args.action_name,
                'action_name_pascal': action_name_pascal,
                'action_type_colon': action_type_colon,
                'action_include_path': action_include_path,
            })

        if node_template:
            node_content = node_template.substitute(**template_vars)
            src_file_path = os.path.join(package_path, "src", f"{node_executable_name}.cpp")
            with open(src_file_path, 'w') as f:
                f.write(node_content)
            print(f"  Created src/{node_executable_name}.cpp")
        else:
            print(f"Warning: No C++ template found for node type '{args.node_type}'. Source file not created.")

    elif args.language == 'py':
        # Create package directory structure
        py_pkg_dir = os.path.join(package_path, args.package_name)
        os.makedirs(py_pkg_dir, exist_ok=True)
        os.makedirs(os.path.join(package_path, "resource"), exist_ok=True)
        os.makedirs(os.path.join(package_path, "test"), exist_ok=True)
        # Python packages often have an empty launch directory or example launch files
        os.makedirs(os.path.join(package_path, "launch"), exist_ok=True)


        # setup.py
        setup_py_content = PY_SETUP_PY_TEMPLATE.substitute(
            package_name=args.package_name,
            node_name=node_name_safe, # Entry point name
            node_executable_name=node_executable_name, # Python module name
            custom_interface_data_files=custom_interface_data_files_py.strip(',') # Remove trailing comma if it exists
        )
        with open(os.path.join(package_path, "setup.py"), 'w') as f:
            f.write(setup_py_content)
        print("  Created setup.py")

        # package.xml
        package_xml_content = PY_PACKAGE_XML_TEMPLATE.substitute(
            package_name=args.package_name,
            xml_dependencies=xml_dependencies
        )
        with open(os.path.join(package_path, "package.xml"), 'w') as f:
            f.write(package_xml_content)
        print("  Created package.xml")

        # setup.cfg
        setup_cfg_content = PY_SETUP_CFG_TEMPLATE.substitute(package_name=args.package_name)
        with open(os.path.join(package_path, "setup.cfg"), 'w') as f:
            f.write(setup_cfg_content)
        print("  Created setup.cfg")

        # resource/<package_name>
        with open(os.path.join(package_path, "resource", args.package_name), 'w') as f:
            f.write(PY_RESOURCE_MARKER_TEMPLATE) # Empty file
        print(f"  Created resource/{args.package_name}")

        # <package_name>/__init__.py
        with open(os.path.join(py_pkg_dir, "__init__.py"), 'w') as f:
            f.write(PY_INIT_PY_TEMPLATE) # Empty file
        print(f"  Created {args.package_name}/__init__.py")

        # Test files
        maintainer = "user" # Default maintainer for templates
        with open(os.path.join(package_path, "test", "test_copyright.py"), 'w') as f:
            f.write(PY_TEST_COPYRIGHT_TEMPLATE.substitute(maintainer=maintainer))
        with open(os.path.join(package_path, "test", "test_flake8.py"), 'w') as f:
            f.write(PY_TEST_FLAKE8_TEMPLATE.substitute(maintainer=maintainer))
        with open(os.path.join(package_path, "test", "test_pep257.py"), 'w') as f:
            f.write(PY_TEST_PEP257_TEMPLATE.substitute(maintainer=maintainer))
        print("  Created test files (copyright, flake8, pep257)")


        # Node script file
        node_template = None
        template_vars = {
            'node_name': node_name_safe,
            'node_class_name': node_class_name,
            'package_name': args.package_name,
        }
        if args.node_type == 'publisher':
            node_template = PY_PUBLISHER_NODE_TEMPLATE
            template_vars.update({
                'topic_name': args.topic_name,
                'msg_module': msg_module,
                'msg_class': msg_class,
            })
        elif args.node_type == 'subscriber':
            node_template = PY_SUBSCRIBER_NODE_TEMPLATE
            template_vars.update({
                'topic_name': args.topic_name,
                'msg_module': msg_module,
                'msg_class': msg_class,
            })
        elif args.node_type == 'service_server':
            node_template = PY_SERVICE_SERVER_NODE_TEMPLATE
            template_vars.update({
                'service_name': args.service_name,
                'srv_module': srv_module,
                'srv_class': srv_class,
            })
        elif args.node_type == 'service_client':
            node_template = PY_SERVICE_CLIENT_NODE_TEMPLATE
            template_vars.update({
                'service_name': args.service_name,
                'srv_module': srv_module,
                'srv_class': srv_class,
            })
        elif args.node_type == 'action_server':
            node_template = PY_ACTION_SERVER_NODE_TEMPLATE
            template_vars.update({
                'action_name': args.action_name,
                'action_module': action_module,
                'action_class': action_class,
            })
        elif args.node_type == 'action_client':
            node_template = PY_ACTION_CLIENT_NODE_TEMPLATE
            template_vars.update({
                'action_name': args.action_name,
                'action_module': action_module,
                'action_class': action_class,
            })

        if node_template:
            node_content = node_template.substitute(**template_vars)
            script_file_path = os.path.join(py_pkg_dir, f"{node_executable_name}.py")
            with open(script_file_path, 'w') as f:
                f.write(node_content)
            make_executable(script_file_path) # Make the script executable
            print(f"  Created {args.package_name}/{node_executable_name}.py and made it executable")
        else:
            print(f"Warning: No Python template found for node type '{args.node_type}'. Script file not created.")
    else:
        print(f"Error: Unsupported language '{args.language}'. Choose 'cpp' or 'py'.")
        sys.exit(1)

    print(f"Package '{args.package_name}' created successfully in '{package_path}'.")
    print("Remember to add this package to your ROS2 workspace and build it (e.g., `colcon build`).")


def main():
    parser = argparse.ArgumentParser(description="Generate ROS2 package templates.")
    parser.add_argument("language", choices=['cpp', 'py'], help="Programming language (cpp or py)")
    parser.add_argument("package_name", help="Name of the ROS2 package to create")
    parser.add_argument("node_type", choices=['publisher', 'subscriber', 'service_server', 'service_client', 'action_server', 'action_client'],
                        help="Type of ROS2 node template to generate")

    parser.add_argument("--node-name", help="Name for the node (and executable/script). Defaults to <package_name>_<node_type>_node")
    parser.add_argument("--target-path", default=".", help="Directory where the package will be created. Defaults to current directory.")

    # Type specific arguments
    parser.add_argument("--topic-name", default="topic", help="Topic name for publisher/subscriber")
    parser.add_argument("--msg-type", default="std_msgs/msg/String", help="Message type for publisher/subscriber (e.g., std_msgs/msg/String)")

    parser.add_argument("--service-name", default="service", help="Service name for service server/client")
    parser.add_argument("--srv-type", default="CustomSrv", help="Service type (e.g., example_interfaces/srv/AddTwoInts or MySrv for custom within package)")

    parser.add_argument("--action-name", default="action", help="Action name for action server/client")
    parser.add_argument("--action-type", default="CustomAction", help="Action type (e.g., action_tutorials_interfaces/action/Fibonacci or MyAction for custom)")

    args = parser.parse_args()

    # Set default node name if not provided
    if not args.node_name:
        args.node_name = f"{args.package_name}_{args.node_type}_node"

    # Clean up node name (Python scripts cannot have hyphens)
    args.node_name = args.node_name.replace("-", "_")


    # Validate msg_type format
    if args.node_type in ['publisher', 'subscriber']:
        try:
            parse_ros_type(args.msg_type)
        except ValueError:
            print(f"Error: Invalid --msg-type format '{args.msg_type}'. Expected 'package/type_category/TypeName' (e.g., 'std_msgs/msg/String').")
            sys.exit(1)

    # Validate srv_type format (if it contains '/', assume it's full path)
    if args.node_type in ['service_server', 'service_client'] and '/' in args.srv_type:
        try:
            parse_ros_type(args.srv_type)
        except ValueError:
            print(f"Error: Invalid --srv-type format '{args.srv_type}'. Expected 'package/type_category/TypeName' or 'TypeName' for custom.")
            sys.exit(1)

    # Validate action_type format (if it contains '/', assume it's full path)
    if args.node_type in ['action_server', 'action_client'] and '/' in args.action_type:
        try:
            parse_ros_type(args.action_type)
        except ValueError:
            print(f"Error: Invalid --action-type format '{args.action_type}'. Expected 'package/type_category/TypeName' or 'TypeName' for custom.")
            sys.exit(1)


    create_package_files(args)


if __name__ == "__main__":
    main()
```
