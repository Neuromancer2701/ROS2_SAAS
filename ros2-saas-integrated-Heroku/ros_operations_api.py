import sys
import os
import json
import subprocess
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the base directory for source projects.
# This script assumes it's located at the root of the Heroku project,
# and the ROS projects are in a subdirectory named 'src_projects'.
SRC_PROJECTS_DIR = Path(__file__).parent / "src_projects"

def run_command(command_args, working_dir=None, env=None):
    """Helper function to run shell commands and capture output."""
    try:
        process = subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
            env=env
        )
        stdout, stderr = process.communicate(timeout=120) # 120 seconds timeout
        return {
            "returncode": process.returncode,
            "stdout": stdout.strip(),
            "stderr": stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1, # Custom code for timeout
            "stdout": "",
            "stderr": "Command timed out after 120 seconds."
        }
    except Exception as e:
        return {
            "returncode": -2, # Custom code for other exceptions
            "stdout": "",
            "stderr": f"Failed to execute command: {e}"
        }

def get_ros_env():
    """
    Sets up a basic ROS environment.
    On Heroku, a full ROS environment isn't typically available.
    This function would need to point to a pre-built ROS overlay if one exists
    in the Docker image, or it might be minimal if only non-runtime tools are used.
    """
    ros_env = os.environ.copy()
    # If ROS is installed in a specific path in the Docker image (e.g., /opt/ros/jazzy)
    ros_setup_path = "/opt/ros/jazzy/setup.bash"
    if os.path.exists(ros_setup_path):
        # This method of sourcing in Python is tricky and often doesn't work as expected
        # for setting the environment for subprocesses directly.
        # It's better if the Docker container's global environment is already set up,
        # or if individual commands are wrapped with `source setup.bash && your_command`.
        # For now, we'll assume PATH and Python paths might be set if rclpy is used.
        # This is more for tools like `colcon` or `ros2 pkg` if they were used directly.
        ros_env["AMENT_PREFIX_PATH"] = ros_env.get("AMENT_PREFIX_PATH", "") + f":{SRC_PROJECTS_DIR}/ros2_saas_ide_config/ros2_ws/install" # Example
        # Add more paths if other pre-built workspaces are available and needed.
    # logging.info(f"ROS Environment (conceptual): {ros_env.get('AMENT_PREFIX_PATH', 'Not set')}")
    return ros_env

def handle_package_generation(args):
    """
    Handles requests related to ROS2 package generation.
    Invokes the script from 'ros2-package-generator'.
    """
    logging.info(f"Handling package generation with args: {args}")

    generator_script = SRC_PROJECTS_DIR / "ros2-package-generator" / "src" / "ros2_pkg_gen.py"
    if not generator_script.exists():
        return {"success": False, "error": "Package generator script not found.", "details": str(generator_script)}

    # Args for ros2_pkg_gen.py: language, package_name, node_type, [options]
    # Example: args = ["cpp", "my_test_pkg", "publisher", "--node-name", "my_talker"]
    if len(args) < 3:
        return {"success": False, "error": "Insufficient arguments for package generation. Need language, package_name, node_type."}

    # Define a temporary output path within Heroku's ephemeral filesystem
    # This path needs to be accessible and writable.
    # Generated files would ideally be zipped and returned or stored elsewhere.
    temp_output_path = Path("/tmp/generated_ros_packages")
    temp_output_path.mkdir(parents=True, exist_ok=True)

    command = ["python3", str(generator_script)] + args + ["--target-path", str(temp_output_path)]

    logging.info(f"Executing command: {' '.join(command)}")
    result = run_command(command)

    if result["returncode"] == 0:
        package_name = args[1]
        generated_package_path = temp_output_path / package_name
        # For Heroku, we can't just give a path. We might list files or zip and offer download (complex via this script).
        # For now, just confirm creation and list contents.
        if generated_package_path.exists() and generated_package_path.is_dir():
            package_contents = [str(p.relative_to(temp_output_path)) for p in generated_package_path.rglob('*')]
            return {
                "success": True,
                "message": f"Package '{package_name}' generated successfully in temporary location.",
                "output_path_on_server": str(generated_package_path), # This path is ephemeral
                "package_contents": package_contents,
                "stdout": result["stdout"],
                "stderr": result["stderr"]
            }
        else:
            return {
                "success": False,
                "error": f"Package generation script ran, but output directory '{generated_package_path}' not found.",
                "stdout": result["stdout"],
                "stderr": result["stderr"]
            }
    else:
        return {
            "success": False,
            "error": "Package generation failed.",
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"]
        }

def handle_list_workspace_projects(args):
    """Lists the projects copied into src_projects."""
    logging.info("Handling list_workspace_projects request.")
    try:
        projects = [d.name for d in SRC_PROJECTS_DIR.iterdir() if d.is_dir()]
        return {"success": True, "projects": projects}
    except Exception as e:
        return {"success": False, "error": f"Failed to list projects: {str(e)}"}

def handle_get_file_content(args):
    """
    Reads content of a file from one of the src_projects.
    args: ["project_name", "relative_file_path"]
    """
    logging.info(f"Handling get_file_content with args: {args}")
    if len(args) < 2:
        return {"success": False, "error": "Insufficient arguments. Need project_name and relative_file_path."}

    project_name = args[0]
    relative_file_path = args[1]

    file_path = SRC_PROJECTS_DIR / project_name / relative_file_path

    if not file_path.exists() or not file_path.is_file():
        # Try to resolve potential path issues, e.g. if project_name itself is part of relative_file_path
        alt_file_path = SRC_PROJECTS_DIR / relative_file_path
        if alt_file_path.exists() and alt_file_path.is_file() and project_name in str(alt_file_path):
             file_path = alt_file_path
        else:
            return {"success": False, "error": f"File not found or is not a file: {file_path} (and alternative checks failed)"}

    try:
        content = file_path.read_text(encoding='utf-8')
        return {"success": True, "file_path": str(file_path), "content": content}
    except Exception as e:
        return {"success": False, "error": f"Failed to read file {file_path}: {str(e)}"}


def main():
    """
    Main function to process commands passed from Node.js server.
    Expected sys.argv:
    [0]: script_name (ros_operations_api.py)
    [1]: command (e.g., "generate_package", "list_projects")
    [2:]: arguments for the command
    """
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No command provided to ros_operations_api.py."}))
        sys.exit(1)

    command = sys.argv[1]
    command_args = sys.argv[2:]
    response = {}

    logging.info(f"Python API received command: '{command}' with args: {command_args}")

    if command == "generate_package":
        response = handle_package_generation(command_args)
    elif command == "list_projects":
        response = handle_list_workspace_projects(command_args)
    elif command == "get_file_content":
        response = handle_get_file_content(command_args)
    # Add more commands here as needed:
    # elif command == "build_workspace":
    #   response = handle_build_workspace(command_args) # Needs colcon, ROS env
    # elif command == "run_simulation":
    #   response = handle_run_simulation(command_args) # Needs Gazebo, ROS env, X server (not on Heroku)
    else:
        response = {"success": False, "error": f"Unknown command: {command}"}

    # Output response as JSON to stdout, for Node.js to capture
    print(json.dumps(response))

if __name__ == "__main__":
    main()
```

This Python script `ros_operations_api.py` provides a basic CLI-like interface that can be called from the Node.js backend.
- It uses `subprocess` to run commands, specifically for the package generator.
- It includes placeholders or considerations for a ROS environment, acknowledging the limitations on Heroku.
- It can list the "projects" (which are the directories copied into `src_projects`).
- It can read file content from these projects.
- It outputs JSON, which the Node.js `server.js` is set up to parse.

This script **does not** attempt to run a live ROS graph or Gazebo, as that's generally unsuitable for Heroku. Its "ROS operations" are limited to things like invoking code generation scripts or file system operations on the copied project files. More complex ROS interactions would require `rclpy` and communication with an external ROS system, or a more capable (non-Heroku) deployment environment.
