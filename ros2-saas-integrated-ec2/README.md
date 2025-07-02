# ROS2 SaaS Platform - AWS EC2/ECS Integrated Deployment

This repository provides configurations and templates for deploying the ROS2 SaaS application platform on Amazon Web Services (AWS), primarily focusing on using EC2 (potentially GPU-enabled instances like g4dn for Gazebo) and ECS Fargate for container orchestration, with RDS for PostgreSQL as the database.

## Deployment Strategy

1.  **Infrastructure as Code (IaC):** An AWS CloudFormation template (`cloudformation.yaml`) is provided to provision the core infrastructure:
    *   VPC, Subnets, Security Groups (parameters).
    *   RDS PostgreSQL instance.
    *   ECS Cluster.
    *   ECS Task Definition for Fargate (to run the application Docker container).
    *   ECS Service (Fargate-based).
    *   Optionally, an EC2 instance (e.g., for a dedicated Gazebo server or bastion host).

2.  **Dockerization:**
    *   A `Dockerfile` is included to build the application image. This image contains ROS2 Jazzy, Gazebo, Node.js, and the application code.
    *   The `entrypoint_aws.sh` script handles container initialization.

3.  **CI/CD with GitHub Actions for ECR:**
    *   A GitHub Actions workflow (`.github/workflows/aws_ecr_push.yml`) is provided to:
        *   Build the Docker image using the `Dockerfile`.
        *   Push the built image to Amazon Elastic Container Registry (ECR).
        *   This workflow assumes a monorepo structure where it can access source code from other phase directories (e.g., `ros2-front-end`, `ros2-package-generator`) to be included in the Docker image.

4.  **Source Code Management for Deployment:**
    *   The GitHub Actions workflow is responsible for packaging the application code (from all relevant phases 1-6) into the Docker image.
    *   The `Dockerfile` will contain `COPY` instructions to include code from `ros2-front-end/`, the Node.js backend, the Python API layer, and any necessary ROS packages from `ros2-package-generator/`, `ros2-gazebo-integration/`, etc., into the image. These ROS packages would typically be built within a multi-stage Dockerfile or copied as pre-built artifacts into the final image.

5.  **Application Execution:**
    *   **ECS Fargate (Primary):** The CloudFormation template sets up an ECS service to run the Docker container (pulled from ECR) using AWS Fargate. This is suitable for the web frontend, Node.js backend, and Python API layer.
    *   **EC2 (Optional/Hybrid):** For resource-intensive tasks like running a full Gazebo simulation server, the CloudFormation template includes an optional EC2 instance definition (e.g., a `g4dn` GPU instance). The application components running on ECS/Fargate could then communicate with services (like Gazebo server) running on this EC2 instance over the network.

## Included Files in This Phase

-   **`Dockerfile`**: Builds the main application image for AWS, including ROS2, Gazebo, Node.js, and application code.
-   **`entrypoint_aws.sh`**: Entrypoint script for the Docker container, handling environment setup and service startup.
-   **`cloudformation.yaml`**: AWS CloudFormation template to provision infrastructure (RDS, ECS Cluster, ECS Service, optional EC2).
-   **`.github/workflows/aws_ecr_push.yml`**: GitHub Actions workflow to build the Docker image and push it to AWS ECR.
-   **`README.md`**: This file.

## Deployment Instructions

### Prerequisites

1.  AWS Account.
2.  AWS CLI configured locally with necessary permissions, or IAM OIDC set up for GitHub Actions.
3.  Docker installed locally (for testing image builds).
4.  An ECR repository created in your AWS account (e.g., `ros2-saas-app`). The GitHub Actions workflow will push to this.
5.  A VPC and Subnets in your AWS account. These will be inputs to the CloudFormation template.
6.  An EC2 KeyPair (if you plan to use the optional EC2 instance and want SSH access).
7.  This repository (`ros2-saas-integrated-ec2`) cloned, along with access to the source code of projects from Phases 1-6 (ideally in a monorepo structure where this project is a part).

### Steps

#### 1. Prepare Your Monorepo Structure (If not already done)

Ensure that this `ros2-saas-integrated-ec2` directory and the directories for Phases 1-6 (e.g., `ros2-front-end`, `ros2-package-generator`, `ros2-gazebo-integration`, etc.) are part of the same parent Git repository (monorepo). The GitHub Actions workflow and Dockerfile `COPY` commands rely on this structure to correctly package all necessary code.

Example monorepo root structure:
```
.
├── ros2-saas-ide-config/
├── ros2-package-generator/
├── ros2-gazebo-integration/
├── ros2-debug-tools/
├── ros2-cicd-pipeline/  (contains general CI concepts, not directly used by this AWS phase's CI)
├── ros2-front-end/
├── ros2-saas-integrated-heroku/
├── ros2-saas-integrated-digital-ocean/
├── ros2-saas-integrated-ec2/       <-- You are here
│   ├── Dockerfile
│   ├── entrypoint_aws.sh
│   ├── cloudformation.yaml
│   ├── .github/workflows/aws_ecr_push.yml
│   └── README.md
... (other integration phases)
```
The `Dockerfile` in `ros2-saas-integrated-ec2/` will use commands like `COPY ../ros2-front-end /opt/ros2_saas_app/frontend/` assuming the build context is the monorepo root.

#### 2. Configure GitHub Actions Secrets for AWS ECR Push

-   Go to your GitHub repository settings > Secrets and Variables > Actions.
-   **If using IAM OIDC (Recommended):**
    *   Ensure an IAM OIDC provider is configured in your AWS account for GitHub Actions.
    *   Create an IAM Role that the GitHub Actions workflow can assume. This role needs permissions to push to ECR (e.g., `AmazonEC2ContainerRegistryPowerUser` or a more fine-grained policy).
    *   Add the following secrets in GitHub:
        *   `AWS_ACCOUNT_ID`: Your 12-digit AWS Account ID.
        *   `AWS_IAM_ROLE_NAME`: The name of the IAM Role created for GitHub Actions.
-   **If using Access Keys (Less Secure):**
    *   Create an IAM user with programmatic access and permissions to push to ECR.
    *   Add the following secrets in GitHub:
        *   `AWS_ACCESS_KEY_ID`: The Access Key ID of the IAM user.
        *   `AWS_SECRET_ACCESS_KEY`: The Secret Access Key of the IAM user.
        *   `AWS_SESSION_TOKEN` (Optional): If using temporary credentials.

Update the `aws_ecr_push.yml` workflow file if you change region or ECR repository name.

#### 3. Customize Dockerfile and Entrypoint (If Needed)

-   Review `ros2-saas-integrated-ec2/Dockerfile` and `ros2-saas-integrated-ec2/entrypoint_aws.sh`.
-   Ensure the `Dockerfile` correctly copies all necessary application code from the other phase directories (relative to the monorepo root build context).
-   Modify `entrypoint_aws.sh` to start your specific ROS nodes, Node.js backend, or other services as required.

#### 4. Run the GitHub Actions Workflow to Build and Push to ECR

-   Commit and push your changes to the branch specified in `aws_ecr_push.yml` (e.g., `main`).
-   The workflow will automatically trigger, build the Docker image, and push it to your ECR repository.
-   Note the image tag used (typically the commit SHA).

#### 5. Deploy Infrastructure with CloudFormation

-   Navigate to the AWS CloudFormation console.
-   Click "Create stack" > "With new resources (standard)".
-   Upload the `ros2-saas-integrated-ec2/cloudformation.yaml` template file.
-   Fill in the parameters:
    *   `VpcId`, `SubnetIds`: Your existing network configuration.
    *   `InstanceType`, `EC2ImageId`, `KeyPairName`: For the optional EC2 instance. **Update `EC2ImageId` to a suitable AMI for your region and needs (e.g., Ubuntu 20/22 based Deep Learning AMI for GPU instances).**
    *   `DBInstanceClass`, `DBAllocatedStorage`, `DBName`, `DBUsername`, `DBPassword`: For the RDS PostgreSQL database.
    *   `EcrRepositoryName`: The name of your ECR repository.
    *   `DockerImageTag`: The tag of the image pushed by GitHub Actions (e.g., the commit SHA or `latest`).
    *   `ContainerCpu`, `ContainerMemory`: For ECS Fargate tasks.
-   Review and create the stack. This will take some time to provision all resources.

#### 6. Accessing the Application

-   **ECS Service:** If you've configured an Application Load Balancer (ALB) in front of your ECS service (recommended, but not fully detailed in this basic template), use the ALB's DNS name. If the ECS service tasks have public IPs and are directly exposed (as per the basic template for simplicity), you can find the public IP of a task in the ECS console.
-   **EC2 Instance (if created):** Use its Public IP address (from EC2 console or CloudFormation outputs) to access services hosted directly on it (e.g., if you set up Nginx there or for SSH).
-   **Database:** The application running in ECS/EC2 will connect to RDS using the endpoint provided in CloudFormation outputs and environment variables.

### Managing and Updating

-   **Application Updates:** Push new code, let the GitHub Actions workflow build and push a new image to ECR. Then, update the ECS service to use the new image tag (this can be automated by adding an `aws ecs update-service` command to the GitHub Actions workflow).
-   **Infrastructure Updates:** Modify the `cloudformation.yaml` template and update the stack in the CloudFormation console.

### Important Considerations

-   **Cost:** Be mindful of the cost of AWS services (EC2, RDS, ECS Fargate, ECR, data transfer, etc.). Use the AWS Pricing Calculator.
-   **Security:** Follow AWS security best practices. Restrict Security Group rules, use IAM roles with least privilege, manage secrets securely (e.g., AWS Secrets Manager for database passwords instead of plain text in CloudFormation parameters for production).
-   **GPU on EC2 for Gazebo:** If using a `g4dn` or similar GPU instance for Gazebo server:
    *   Ensure the chosen AMI has NVIDIA drivers installed, or install them via EC2 UserData.
    *   Install `nvidia-container-toolkit` on the EC2 host.
    *   Run Docker containers with the `--gpus all` flag.
    *   The application in ECS might communicate with this Gazebo server over the VPC network.
-   **Logging and Monitoring:** Configure CloudWatch Logs for your ECS tasks (as done in the template) and EC2 instances. Use CloudWatch Metrics and Alarms for monitoring.
-   **Networking:** For complex setups (e.g., ECS tasks communicating with Gazebo on EC2), ensure proper VPC routing, security group rules, and potentially service discovery mechanisms (like AWS Cloud Map).

This AWS deployment provides a robust and scalable platform. Tailor the CloudFormation template, Dockerfile, and workflow to your specific application needs.
```
