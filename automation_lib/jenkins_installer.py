import os
import sys
import shlex
import tempfile
import shutil
import subprocess
import yaml


class JenkinsInstaller:

    def __init__(self, ssh_manager, jenkins_user, jenkins_pass, config_repo_url):
        self.ssh_manager = ssh_manager
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass
        self.config_repo_url = config_repo_url
        self.api_token = os.getenv('H_API_TOKEN')
        self.dns_api_token = os.getenv('H_DNS_API_TOKEN')
        self.ssh_private_key = os.getenv('H_SSH_PRIVATE_KEY')
        self.local_repo_path = None
        

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
            
    def clone_config_repo_local(self):
        self.local_repo_path = tempfile.mkdtemp()
        try:
            clone_cmd = (f"git clone {self.config_repo_url} {self.local_repo_path}")
            subprocess.run(clone_cmd, shell=True, check=True)
            print(f"Config repo cloned to {self.local_repo_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning config repo: {e}")
            sys.exit(1)
            
    def cleanup_local_repo(self):
        if self.local_repo_path and os.path.exists(self.local_repo_path):
            shutil.rmtree(self.local_repo_path)

    def build_jenkins_docker_image(self):
        self.ssh_manager.execute_command(
            "sudo docker build -t jenkins-image /var/jenkins_home/jenkins_configs")

    def clone_config_repo(self):
        self.ssh_manager.execute_command(
        f"git clone {self.config_repo_url} /var/jenkins_home/jenkins_configs")
        
    def read_key_file(self, key_file):
        with open(key_file, 'r') as file:
            key_content = file.read()
        return key_content
    
    def parse_jenkins_yaml_files(self):
        agents = []
        yaml_files = []
        # Collect all YAML files in the specified repository path
        for root, dirs, files in os.walk(self.local_repo_path):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    yaml_file = os.path.join(root, file)
                    yaml_files.append(yaml_file)
        # For each YAML file found, parse its content and create a dictionary for each agent node
        # containing the YAML file path, node index, and node data
        for yaml_file in yaml_files:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            if data and 'jenkins' in data and 'nodes' in data['jenkins']:
                nodes = data['jenkins']['nodes']
                for index, node in enumerate(nodes):
                    if 'permanent' in node:
                        launcher = node['permanent'].get('launcher', {})
                        if 'ssh' in launcher:
                            agents.append({
                                'yaml_file': yaml_file,
                                'node_index': index,
                                'node_data': node
                            })
        return agents



    def run_jenkins_container(self):
        domain = os.getenv('DOMAIN')
        api_token_escaped = shlex.quote(self.api_token)
        dns_api_token_escaped = shlex.quote(self.dns_api_token)
        ssh_key_escaped = shlex.quote(self.ssh_key_content)
        self.ssh_manager.execute_command(
            f"sudo docker run -d --name jenkins "
            f"-p 8080:8080 -p 50000:50000 "
            f"-v jenkins_home:/var/jenkins_home "
            f"-v /var/run/docker.sock:/var/run/docker.sock "
            f"-e ADMIN_USER='{self.jenkins_user}' "
            f"-e ADMIN_PASS='{self.jenkins_pass}' "
            f"-e DOMAIN='https://{domain}' "
            f"-e API_TOKEN={api_token_escaped} "
            f"-e DNS_API_TOKEN={dns_api_token_escaped} "
            f"-e SSH_PRIVATE_KEY={ssh_key_escaped} "
            "jenkins-image"
        )

    def install_jenkins(self):
        self.install_docker()
        self.clone_config_repo()
        self.build_jenkins_docker_image()
        self.ssh_key_content = self.read_key_file(self.ssh_private_key)
        self.run_jenkins_container()