# ROS2 CI/CD Pipeline with GitHub Actions

This directory contains resources for setting up a Continuous Integration and Continuous Deployment (CI/CD) pipeline for a ROS2 application (supporting both C++ and Python packages) using GitHub Actions. It includes:

1.  **A GitHub Actions workflow file** (`.github/workflows/main.yml`): Defines the CI/CD pipeline for building, testing, and packaging a ROS2 application.
2.  **A Dockerfile** (`Dockerfile.ros2-build`): Used by the GitHub Actions workflow to create a consistent build environment for ROS2 Jazzy Jalisco. This Dockerfile is tailored for building and testing, not necessarily for final deployment, though it can be adapted.
3.  **A Dockerfile for deployment** (`Dockerfile.deploy`): A more minimal Dockerfile example for packaging the ROS2 application for deployment after it has been built and tested.

## CI/CD Pipeline Overview (GitHub Actions)

The `main.yml` workflow is typically triggered on pushes to the `main` branch and on pull requests targeting `main`. It performs the following stages:

1.  **Setup:**
    *   Checks out the repository code.
    *   Sets up the Docker build environment using `Dockerfile.ros2-build`.

2.  **Build:**
    *   Installs ROS2 dependencies using `rosdep`.
    *   Builds all ROS2 packages in the workspace using `colcon build`.

3.  **Test:**
    *   Runs linters (e.g., `ament_cpplint`, `ament_flake8`).
    *   Executes tests defined in the packages using `colcon test`.
    *   Uploads test results as artifacts.

4.  **Package (Conceptual - for Deployment):**
    *   (If tests pass on `main` branch) Builds a deployment Docker image using `Dockerfile.deploy`.
    *   (Optional) Pushes the deployment image to a Docker registry (e.g., Docker Hub, GitHub Container Registry). This step usually requires secrets for registry authentication.

## Files

### 1. `.github/workflows/main.yml`

This file defines the GitHub Actions workflow. Key features:
- Runs on Ubuntu latest.
- Uses Docker to ensure a consistent ROS2 Jazzy environment.
- Caches `ccache` and `colcon_ws/install` to speed up builds.
- Runs `rosdep install` to get dependencies.
- Builds the workspace using `colcon build --symlink-install`.
- Runs tests using `colcon test` and `colcon test-result --verbose`.
- (Optionally) Builds and pushes a deployment Docker image.

**Note:** This file should be placed in the `.github/workflows/` directory *of the ROS2 application repository* that you want to apply this CI/CD pipeline to. For this project structure, it's provided here as a template.

### 2. `Dockerfile.ros2-build`

This Dockerfile sets up a ROS2 Jazzy development and build environment. It includes:
- Base ROS2 Jazzy image.
- Common build tools (`colcon`, `rosdep`, compilers).
- `ccache` for speeding up C++ compilations.
- Initialization of `rosdep`.

This image is used by the GitHub Actions workflow to run build and test steps.

### 3. `Dockerfile.deploy`

This Dockerfile provides a template for creating a deployment image. It typically:
- Starts from a minimal base image (e.g., `ros:jazzy-ros-core` or even a plain Ubuntu and installs only necessary runtime dependencies).
- Copies the built ROS2 application (from the `install` directory of the workspace) into the image.
- Sets up the entrypoint to run the ROS2 application.

This image is intended to be smaller and more secure than the build image.

## Configuration and Usage

1.  **Place files in your ROS2 Application Repository:**
    *   Copy the `Dockerfile.ros2-build` and `Dockerfile.deploy` to the root of your ROS2 application repository (or a suitable location referenced by the workflow).
    *   Create the directory `.github/workflows/` in the root of your ROS2 application repository.
    *   Copy the `main.yml` file into `.github/workflows/main.yml`.

2.  **Customize `main.yml`:**
    *   **ROS Distro:** Ensure the `ROS_DISTRO` environment variable is set correctly (e.g., `jazzy`).
    *   **Triggers:** Adjust the `on:` section to specify when the workflow should run (e.g., pushes to specific branches, pull requests).
    *   **Caching:** Review cache keys for `ccache` and `colcon_ws` to ensure they suit your project.
    *   **Docker Registry (Optional):** If you want to push a deployment image:
        *   Uncomment and configure the "Login to Docker Registry" and "Build and push deployment image" steps.
        *   Add necessary secrets (e.g., `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`) to your GitHub repository's secrets settings.
        *   Update the image name and tags.
    *   **Workspace Path:** If your ROS2 workspace is not at the root of the repository, adjust paths in `colcon` commands (e.g., `colcon build --ws my_ros_ws`).

3.  **Customize `Dockerfile.deploy`:**
    *   Modify it to copy only the necessary installed files from your workspace.
    *   Set up the correct `ENTRYPOINT` or `CMD` to run your application nodes.
    *   Ensure all runtime dependencies are installed.

4.  **Commit and Push:**
    *   Commit these files to your repository and push to GitHub. The workflow should automatically trigger based on the configured events.

## Viewing Workflow Runs

You can view the status and logs of your workflow runs in the "Actions" tab of your GitHub repository.

## Local Testing of Dockerfiles (Optional)

-   **Build Image:**
    ```bash
    docker build -t ros2-build-env -f Dockerfile.ros2-build .
    ```
-   **Deployment Image (requires a built workspace):**
    Assuming your built workspace's `install` directory is in `./colcon_ws/install`:
    ```bash
    docker build -t my-ros-app-deploy -f Dockerfile.deploy --build-arg WORKSPACE_INSTALL_DIR=./colcon_ws/install .
    ```

This CI/CD setup provides a solid foundation for automating the build, test, and deployment of ROS2 applications. Remember to adapt it to the specific needs and structure of your project.
```
