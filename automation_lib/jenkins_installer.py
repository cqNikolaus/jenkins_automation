import os
import sys
import base64


class JenkinsInstaller:

    def __init__(self, ssh_manager, jenkins_user, jenkins_pass, config_repo_url):
        self.ssh_manager = ssh_manager
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass
        self.config_repo_url = config_repo_url
        
        
        self.encoded_api_token = os.getenv('ENCODED_API_TOKEN')
        self.encoded_dns_api_token = os.getenv('ENCODED_DNS_API_TOKEN')
        self.encoded_ssh_private_key = os.getenv('ENCODED_SSH_KEY_FILE')
        
        
        self.api_token = base64.b64decode(self.encoded_api_token).decode('utf-8')
        self.dns_api_token = base64.b64decode(self.encoded_dns_api_token).decode('utf-8')
        self.ssh_private_key = base64.b64decode(self.encoded_ssh_private_key).decode('utf-8')

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
            f"-e ADMIN_USER={self.jenkins_user} "
            f"-e ADMIN_PASS={self.jenkins_pass} "
            f"-e DOMAIN='https://{os.getenv('DOMAIN')}' "
            f"-e API_TOKEN={self.api_token} "
            f"-e DNS_API_TOKEN={self.dns_api_token} "
            f"-e SSH_PRIVATE_KEY={self.ssh_private_key} "
            "jenkins-image"
    )

    def install_jenkins(self):
        print(f"HIERAPITOKEN: {self.api_token}")
        self.install_docker()
        self.clone_config_repo()
        self.copy_dockerfile_to_vm()
        self.build_jenkins_docker_image()
        self.run_jenkins_container()