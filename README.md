
# Jenkins Automation with Hetzner Cloud and Docker

Automate the setup of a Jenkins instance on a Hetzner Cloud VM using Docker, with customizable configurations and automated SSL provisioning.

<br>

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Clone the Repository](#clone-the-repository)
  - [Set Up Environment Variables](#set-up-environment-variables)
  - [Install Dependencies](#install-dependencies)
- [Usage](#usage)
  - [Running the Script](#running-the-script)
  - [Customizing Jenkins Configuration](#customizing-jenkins-configuration)
    - [Customizing the Initial Test Job](#customizing-the-initial-test-job)
- [Environment Variables](#environment-variables)
- [Running in a Jenkins Pipeline](#running-in-a-jenkins-pipeline)
  - [Jenkins Pipeline Requirements](#jenkins-pipeline-requirements) 
  - [Using `create_environment.py` with `Jenkinsfile_setup`](#using-create_environmentpy-with-jenkinsfile_setup)
  - [CI/CD Pipeline with `main.py` and `Jenkinsfile`](#cicd-pipeline-with-mainpy-and-jenkinsfile)
- [Project Structure](#project-structure)
<br>

## Features

- **Automated VM Creation**: Spin up a new VM in Hetzner Cloud with Ubuntu 22.04.
- **Jenkins Installation**: Install Jenkins inside a Docker container on the VM.
- **Custom Jenkins Configuration**: Use your own Jenkins configuration repository to set up plugins and settings.
- **Automated SSL Setup**: Obtain an SSL certificate from Let's Encrypt and configure Nginx as a reverse proxy.
- **Initial Job Execution**: Automatically create and run an initial Jenkins job to verify the setup.
- **Domain Configuration**: Create a DNS record pointing to the Jenkins instance under your specified domain.
- **CI/CD Pipeline Testing**: Validate the entire setup process using a Jenkins pipeline.
<br>

## Prerequisites

- **Python 3.6 or higher**
- **Git**
- **Pip**
- **Hetzner Cloud Account** with API and DNS API tokens
- **SSH Key** registered in Hetzner Cloud
- **Domain Name** managed via Hetzner DNS (or compatible with Hetzner DNS API)
<br>


## Installation

### Clone the Repository

```bash
git clone https://github.com/cqNikolaus/jenkins_automation.git
cd jenkins_automation
```
<br>

### Set Up Environment Variables

Copy the example environment file and fill in your details:

```bash
cp .env.example .env
```

Edit the `.env` file and replace placeholder values with your actual credentials and configurations.

<br>


### Install Dependencies

Create a virtual environment and install required packages:

```bash
python3 -m venv venv
```
```bash
.\venv\Scripts\activate    # Windows
source venv/bin/activate   # Linux/Mac
```
```bash
pip install -r requirements.txt
```
<br>

## Usage

### Running the Script

Execute the `create_environment.py` script with your Jenkins configuration repository:

```bash
python scripts/create_environment.py --config-repo https://github.com/yourusername/yourjenkinsconfigs.git
```

- Replace `https://github.com/yourusername/yourjenkinsconfigs.git` with your Jenkins configuration repository URL.
- Ensure all required environment variables are set, either in the `.env` file or your system environment.

  <br>

### Customizing Jenkins Configuration

You can customize Jenkins by providing your own configuration repository. Your repository should include:

- **plugins.txt**: List of Jenkins plugins to install.
  - Must include the following default plugins:
    ```
    git
    workflow-aggregator
    configuration-as-code
    locale
    job-dsl
    docker-workflow
    ```
- **jenkins.yaml**: Jenkins Configuration as Code file.
  - Use `${JENKINS_USER}` and `${JENKINS_PASS}` placeholders in the `users` section to inject admin credentials from environment variables.
  - Use `${DOMAIN}` in the `location` section if needed.

You can fork and modify the [default Jenkins configurations](https://github.com/cqNikolaus/jenkins_configs) as a starting point.

<br>

#### Customizing the Initial Test Job

The initial test job is defined in the `jenkins.yaml` file using [Job DSL](https://plugins.jenkins.io/job-dsl/) and [Jenkins Configuration as Code (JCasC)](https://plugins.jenkins.io/configuration-as-code/). To customize this job:

- **Modify the Job Definition**: Edit the `jenkins.yaml` file in your configuration repository to change the job's settings, scripts, or parameters according to your needs.
- **Rename the Job**:
  - If you change the job's name in `jenkins.yaml`, you must also update the `JOB_NAME` environment variable in your `.env` file or system environment to match the new name.
  - This ensures that the script knows which job to trigger and monitor after the setup.

**Example**:

If you rename the job from `docker-test` to `my-custom-job` in `jenkins.yaml`:

- Update the `JOB_NAME` in your `.env` file:

  ```dotenv
  JOB_NAME=my-custom-job
  ```

- Ensure that the job definition in `jenkins.yaml` uses the same name.

**Note**: When customizing the job, adhere to the Job DSL and JCasC guidelines to ensure compatibility.

<br><br>

## Environment Variables

The script relies on several environment variables for configuration. Below is the list of required variables:

| Variable            | Description                                                |
|---------------------|------------------------------------------------------------|
| `API_TOKEN`         | Hetzner Cloud API token                                    |
| `DNS_API_TOKEN`     | Hetzner DNS API token                                      |
| `DOMAIN`            | Full domain for the Jenkins instance (e.g., `jenkins.example.com`) |
| `ZONE_NAME`         | DNS zone name (e.g., `example.com`)                        |
| `SSH_KEY_NAME`      | Name or ID of your SSH key in Hetzner Cloud                |
| `SSH_PRIVATE_KEY`   | Your private SSH key (enclosed in double quotes)           |
| `JENKINS_USER`      | Jenkins admin username                                     |
| `JENKINS_PASS`      | Jenkins admin password                                     |
| `JOB_NAME`          | Name of the initial Jenkins job to create and run          |
| `SSL_EMAIL`         | Email address for Let's Encrypt SSL certificate            |

<br>

### Example `.env` File

```dotenv
# Hetzner Cloud API Token
API_TOKEN=your_hetzner_api_token_here

# Hetzner DNS API Token
DNS_API_TOKEN=your_hetzner_dns_api_token_here

# Domain for Jenkins instance
DOMAIN=jenkins.example.com

# DNS Zone name
ZONE_NAME=example.com

# SSH Key Name or ID in Hetzner Cloud
SSH_KEY_NAME=your_ssh_key_name_here

# Jenkins Admin Credentials
JENKINS_USER=admin
JENKINS_PASS=your_secure_password

# Private SSH Key for accessing the VM
SSH_PRIVATE_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----"

# Initial Jenkins Job Name
JOB_NAME=docker-test

# Email for SSL Certificate
SSL_EMAIL=youremail@example.com
```

<br>

## Running in a Jenkins Pipeline

You can also run the setup within a Jenkins pipeline, which allows you to automate the entire process as part of your CI/CD workflow.

<br>


### Jenkins Pipeline Requirements

To use the provided Jenkins pipelines (`Jenkinsfile` and `Jenkinsfile_setup`), it is necessary to have a Docker image available in your Jenkins environment. This image must be named **`python-build`** and should contain the following tools pre-installed:

- Python
- Git
- pip
- dnsutils (for DNS checks)
- openssl (for SSL certificate validation)

<br>

### Using `create_environment.py` with `Jenkinsfile_setup`

This method uses the `create_environment.py` script and the `Jenkinsfile_setup` to set up the environment.



#### Steps

1. **Set Up Credentials**: In your Jenkins instance, configure the necessary credentials:
   - **HETZNER_API_TOKEN**: Hetzner Cloud API token
   - **HETZNER_DNS_API_TOKEN**: Hetzner DNS API token
   - **SSH_PRIVATE_KEY**: Your private SSH key
   - **JENKINS_ADMIN_CREDENTIALS**: Jenkins admin username and password



2. **Configure the Pipeline**: Use the provided `Jenkinsfile_setup` in your Jenkins job. Update environment variables as needed.
3. Replace "https://github.com/yourusername/yourjenkinsconfigs.git" in `Jenkinsfile_setup` with your Jenkins configuration repository.

   ```groovy
   pipeline {
       agent {
           docker {
               image 'python:3.8-slim'
               args '-u root:root'
           }
       }
       environment {
           API_TOKEN = credentials('HETZNER_API_TOKEN')
           DNS_API_TOKEN = credentials('HETZNER_DNS_API_TOKEN')
           DOMAIN = "jenkins-${env.BUILD_NUMBER}.example.com"
           ZONE_NAME = "example.com"
           SSH_KEY_NAME = 'your_ssh_key_name_here'
           JOB_NAME = 'docker-test' // Update if you changed the job name
           SSL_EMAIL = 'youremail@example.com'
       }
       stages {
           stage('Setup Environment') {
               steps {
                   withCredentials([
                       sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE'),
                       usernamePassword(credentialsId: 'JENKINS_ADMIN_CREDENTIALS', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS')
                   ]) {
                       sh '''
                           set -e
                           echo "Setting up the environment"
                           chmod 600 $SSH_KEY_FILE
                           export SSH_PRIVATE_KEY="$(cat $SSH_KEY_FILE)"
                           pip install -r requirements.txt
                           python scripts/create_environment.py --config-repo https://github.com/yourusername/yourjenkinsconfigs.git
                       '''
                   }
               }
           }
       }
   }
   ```


4. **Run the Pipeline**: Execute the pipeline, which will:
   - Spin up the VM
   - Install Jenkins in Docker
   - Configure Jenkins with your custom settings
   - Set up DNS and SSL

  
     <br>
     

### CI/CD Pipeline with `main.py` and `Jenkinsfile`

The project also includes a `main.py` script and a `Jenkinsfile` that define a comprehensive CI/CD pipeline for testing the entire environment setup. 

#### Purpose

- **Testing and Validation**: The `main.py` script, along with its `Jenkinsfile`, automates the creation of the Jenkins instance, runs a test job, sets up DNS and SSL, and then tears down the environment.
- **Continuous Integration**: This allows you to ensure that changes to the setup scripts or configurations do not break the deployment process.

#### Steps

1. **Set Up Credentials**: Similar to the previous method, ensure all necessary credentials are configured in your Jenkins instance.


2. **Configure the Pipeline**: Use the provided `Jenkinsfile` in your Jenkins job.

   ```groovy
   pipeline {
     agent {
       docker {
         image 'python:3.8-slim'
         args '-u root:root'
       }
     }
     environment {
       API_TOKEN = credentials('HETZNER_API_TOKEN')
       DNS_API_TOKEN = credentials('HETZNER_DNS_API_TOKEN')
       DOMAIN = "jenkins-${env.BUILD_NUMBER}.example.com"
       ZONE_NAME = "example.com"
       SSH_KEY_NAME = 'your_ssh_key_name_here'
       JOB_NAME = 'docker-test' // Update if you changed the job name
       SSL_EMAIL = 'youremail@example.com'
     }
     stages {
       stage('Create Jenkins Instance') {
         steps {
           withCredentials([
             sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE'),
             usernamePassword(credentialsId: 'JENKINS_ADMIN_CREDENTIALS', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS')
           ]) {
             sh '''
               set -e
               echo "Creating Jenkins instance"
               chmod 600 $SSH_KEY_FILE
               export SSH_PRIVATE_KEY="$(cat $SSH_KEY_FILE)"
               pip install -r requirements.txt
               python scripts/main.py create_jenkins --config-repo https://github.com/yourusername/yourjenkinsconfigs.git
             '''
           }
         }
       }

   [...]

    ```


4. **Run the Pipeline**: This pipeline will:
   - Create the Jenkins instance
   - Run the initial test job
   - Set up DNS and SSL
   - Validate the DNS and SSL configurations
   - Clean up the environment by deleting the VM and DNS records

**Note**: This pipeline is mainly for testing purposes and demonstrates how the entire setup can be automated and validated. 

<br>

## Project Structure

```
jenkins_automation/
├── scripts/
│   ├── create_environment.py    # Main script to set up the environment
│   └── main.py                  # Script defining the CI/CD pipeline for testing
├── automation_lib/
│   ├── __init__.py              # Initialization file for the package
│   ├── vm_manager.py            # Manages VM creation and deletion
│   ├── ssh_manager.py           # Handles SSH connections and commands
│   ├── jenkins_installer.py     # Installs Jenkins on the VM
│   ├── jenkins_job_manager.py   # Manages Jenkins jobs
│   ├── nginx_installer.py       # Sets up Nginx and SSL
│   └── dns_manager.py           # Manages DNS records
├── setup.py                     # Setup script to install automation_lib as a package
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Dockerfile used in Jenkins setup
├── .env.example                 # Example environment variables file
├── Jenkinsfile                  # Jenkinsfile for CI/CD pipeline testing with main.py
├── Jenkinsfile_setup            # Jenkinsfile for running create_environment.py in a Jenkins pipeline
└── README.md                    # Project documentation

```
