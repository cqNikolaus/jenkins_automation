import os
import sys


class JenkinsInstaller:

    def __init__(self, ssh_manager, jenkins_user, jenkins_pass, config_repo_url):
        self.ssh_manager = ssh_manager
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass
        self.config_repo_url = config_repo_url

    def install_docker(self):
        commands = [
            "sudo apt-get update -y",
            "sudo apt-get install -y ca-certificates curl gnupg lsb-release",
            "sudo mkdir -p /etc/apt/keyrings",
            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] '
            'https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | '
            'sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
            "sudo apt-get update -y",
            "sudo apt-get install -y docker-ce docker-ce-cli containerd.io",
            "sudo usermod -aG docker $USER",
            "sudo chmod 666 /var/run/docker.sock"
        ]
        for cmd in commands:
            self.ssh_manager.execute_command(cmd)
            
            
            
    def copy_dockerfile_to_vm(self):
        # Get the current working directory
        local_dockerfile_path = os.path.join(os.getcwd(), 'Dockerfile')
        # Remote path on the VM
        remote_dockerfile_path = '/var/jenkins_home/Dockerfile'

        # Check if Dockerfile exists locally
        if not os.path.isfile(local_dockerfile_path):
            print(f"Local Dockerfile not found at {local_dockerfile_path}")
            sys.exit(1)

        print(f"Copying {local_dockerfile_path} to VM at {remote_dockerfile_path}")
        success = self.ssh_manager.copy_file_to_vm(local_dockerfile_path, remote_dockerfile_path)
        if not success:
            print("Failed to copy Dockerfile to VM")
            sys.exit(1)
        


    def build_jenkins_docker_image(self):
        self.ssh_manager.execute_command(
            "sudo docker build -t jenkins-image /var/jenkins_home")

    def clone_config_repo(self):
        self.ssh_manager.execute_command(
        f"git clone {self.config_repo_url} /var/jenkins_home/jenkins_configs")


    def run_jenkins_container(self):
        self.ssh_manager.execute_command(
            f"sudo docker run -d --name jenkins "
            f"-p 8080:8080 -p 50000:50000 "
            f"-v jenkins_home:/var/jenkins_home "
            f"-v /var/run/docker.sock:/var/run/docker.sock "
            f"-e JENKINS_USER={self.jenkins_user} "
            f"-e JENKINS_PASS={self.jenkins_pass} "
            f"-e DOMAIN='https://{os.getenv('DOMAIN')}' "
            "jenkins-image"
        )

    def install_jenkins(self):
        self.install_docker()
        self.clone_config_repo()
        self.copy_dockerfile_to_vm()
        self.build_jenkins_docker_image()
        self.run_jenkins_container()