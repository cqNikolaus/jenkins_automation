import os

class JenkinsInstaller:

    def __init__(self, ssh_manager, jenkins_user, jenkins_pass):
        self.ssh_manager = ssh_manager
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass

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


    def build_jenkins_docker_image(self):
        self.ssh_manager.execute_command(
            "cd /var/jenkins_home/jenkins-jcac/jenkins-docker && sudo docker build -t jenkins-image .")

    def clone_repo(self):
        repo_url = "https://github.com/cqNikolaus/jenkins_automation"
        self.ssh_manager.execute_command(
            f"git clone --branch module-split {repo_url} /var/jenkins_home/module-split")

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
        self.clone_repo()
        self.build_jenkins_docker_image()
        self.run_jenkins_container()