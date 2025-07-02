# ROS2 SaaS Platform - Heroku Integrated Deployment

This repository consolidates code from the initial ROS2 SaaS development phases and provides configuration for deploying a version of the platform on Heroku.

**Important Note on Heroku and ROS/Gazebo:** Heroku's dynos are primarily designed for web applications and are not well-suited for running full, resource-intensive ROS2 simulations (especially with Gazebo) or long-running, stateful ROS nodes directly. This Heroku integration focuses on:
1.  Deploying the web frontend (`ros2-front-end`).
2.  Running a Node.js backend server.
3.  Providing an API layer (via `ros_operations_api.py`) that can perform non-realtime ROS tasks like invoking the package generator or accessing project files.
4.  Heavy ROS operations (like simulations or complex node interactions) would typically need to be offloaded to a separate, more suitable environment that this Heroku app could potentially communicate with.

## Included Projects (Source Code)

The following projects from previous phases are included in the `src_projects/` directory:
-   `ros2-saas-ide-config`: Dockerfile and scripts for a ROS2 development environment (referenced for context, not directly run on Heroku).
-   `ros2-package-generator`: Python scripts for generating ROS2 package templates. The `ros_operations_api.py` can invoke this.
-   `ros2-gazebo-integration`: ROS2 package for Gazebo simulation with TurtleBot3 (simulation itself won't run on Heroku, but code/launch files can be inspected).
-   `ros2-debug-tools`: Python-based ROS2 debugging dashboard (nodes won't run directly on Heroku, but code can be inspected).
-   `ros2-cicd-pipeline`: GitHub Actions workflow and Dockerfiles (referenced for CI/CD context).
-   `ros2-front-end`: React-based UI, which will be served by the Node.js backend.

## Core Components for Heroku

1.  **`Dockerfile`**:
    *   Sets up a Node.js environment.
    *   Installs Python and basic dependencies.
    *   Copies the application code (Node.js backend, Python API script, and `src_projects/`).
    *   The CMD is set to run the Node.js backend server (`backend/server.js`).

2.  **`Procfile`**:
    *   Defines the `web` process type for Heroku.
    *   Relies on the `CMD` specified in the `Dockerfile` to start the application.

3.  **`package.json`**:
    *   Defines Node.js dependencies (e.g., Express) and scripts.
    *   The `start` script points to `backend/server.js`.

4.  **`backend/server.js`**:
    *   An Express.js application that:
        *   Serves the static files for the `ros2-front-end` UI.
        *   Provides API endpoints (e.g., `/api/ros`, `/api/generate-package`).
        *   Invokes the `ros_operations_api.py` script using `child_process.spawn` to handle ROS-related tasks.

5.  **`ros_operations_api.py`**:
    *   A Python script that acts as a command-line interface, callable by `server.js`.
    *   Handles requests for tasks like:
        *   Generating ROS2 packages using scripts from `ros2-package-generator`.
        *   Listing available projects within `src_projects/`.
        *   Reading file content from projects in `src_projects/`.
    *   It does **not** run live ROS nodes or simulations.

## Deployment to Heroku

### Prerequisites

1.  Heroku Account: [https://signup.heroku.com/](https://signup.heroku.com/)
2.  Heroku CLI: [https://devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3.  Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
4.  Docker Desktop (optional, for local testing of the Dockerfile): [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

### Deployment Steps

1.  **Clone this repository (or your fork):**
    ```bash
    git clone <your-repository-url>
    cd ros2-saas-integrated-Heroku
    ```

2.  **Log in to Heroku CLI:**
    ```bash
    heroku login
    ```

3.  **Create a Heroku App:**
    Choose a unique name for your app.
    ```bash
    heroku create your-app-name
    ```
    This also adds a `heroku` git remote to your local repository.

4.  **Set the Stack to Container:**
    Heroku needs to know you're deploying a Docker container.
    ```bash
    heroku stack:set container -a your-app-name
    ```

5.  **Provision a Heroku PostgreSQL Database (Optional):**
    If your application requires a database (the current Node.js backend doesn't explicitly use one, but a full SaaS app would):
    ```bash
    heroku addons:create heroku-postgresql:hobby-dev -a your-app-name
    ```
    This will add a PostgreSQL database and set a `DATABASE_URL` environment variable in your Heroku app's configuration. Your Node.js application would then need to be configured to use this `DATABASE_URL` (e.g., using the `pg` npm package).

    *To connect to this database from your application (e.g., in `backend/server.js` or a database module):*
    ```javascript
    // Example using 'pg' library in Node.js
    // const { Client } = require('pg');
    // const client = new Client({
    //   connectionString: process.env.DATABASE_URL,
    //   ssl: {
    //     rejectUnauthorized: false // Required for Heroku Postgres connections from Node.js
    //   }
    // });
    // client.connect();
    // client.query('SELECT NOW()', (err, res) => {
    //   if (err) throw err;
    //   console.log('Connected to PostgreSQL:', res.rows[0]);
    //   client.end();
    // });
    ```

6.  **Deploy the Application:**
    Push your code to the `heroku` remote. Heroku will detect the `Dockerfile` and build your image, then deploy it.
    ```bash
    git push heroku main # Or your default branch, e.g., master
    ```
    Monitor the build and deployment process in your terminal or on the Heroku Dashboard.

7.  **Open Your Application:**
    Once deployed, you can open your app in a browser:
    ```bash
    heroku open -a your-app-name
    ```

8.  **View Logs:**
    To troubleshoot or monitor your application:
    ```bash
    heroku logs --tail -a your-app-name
    ```

## Local Development and Testing (Conceptual)

While a full ROS environment is not replicated on Heroku:

1.  **Node.js Backend:** You can run the Node.js backend locally:
    ```bash
    npm install
    npm start
    ```
    This will serve the `ros2-front-end` and allow you to test API calls to `ros_operations_api.py`.

2.  **Python API Script:** Test `ros_operations_api.py` directly:
    ```bash
    python3 ros_operations_api.py list_projects
    python3 ros_operations_api.py generate_package cpp my_test_pkg publisher --node-name test_node
    python3 ros_operations_api.py get_file_content ros2-saas-ide-config README.md
    ```

3.  **Docker Build (Local):**
    You can build the Heroku Docker image locally to check for issues:
    ```bash
    docker build -t ros2-saas-heroku-image .
    # Run it (Heroku sets PORT, so simulate it):
    docker run -p 3000:3000 -e PORT=3000 ros2-saas-heroku-image
    ```
    Then access `http://localhost:3000` in your browser.

## Limitations and Considerations

-   **No Direct Gazebo/Simulation:** Gazebo and intensive ROS simulations cannot run directly on Heroku dynos. The UI's "Run Simulation" button would need to trigger a simulation in an external environment.
-   **Ephemeral Filesystem:** Heroku dynos have an ephemeral filesystem. Any files written (like generated packages in `/tmp`) will be lost when the dyno restarts. For persistent storage, use Heroku Postgres, AWS S3, or similar services.
-   **ROS Network:** Standard ROS2 discovery and communication (DDS) will not work across different Heroku dynos or between Heroku and external ROS systems without significant network configuration (e.g., VPN, DDS routing), which is complex and often outside typical Heroku use cases.
-   **Resource Constraints:** Free/hobby dynos have limitations on CPU, memory, and uptime.

This Heroku deployment provides a way to host the web interface and a backend that can orchestrate simpler, non-realtime ROS-related tasks. For a full-fledged ROS SaaS platform with live simulations, a more robust infrastructure (like Kubernetes on DigitalOcean, AWS, or GCP) would be necessary for the ROS components.
```
