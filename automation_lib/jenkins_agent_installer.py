from automation_lib import SSHManager

class JenkinsAgentInstaller:
    def __init__(self, ssh_manager, jenkins_url, jenkins_user, jenkins_pass):
        self.ssh_manager = ssh_manager
        self.jenkins_url = jenkins_url
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass

    def install_agent(self):
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y openjdk-11-jre-headless",
            "wget --auth-no-challenge --user {} --password '{}' {}/jnlpJars/agent.jar -O agent.jar".format(
                self.jenkins_user, self.jenkins_pass, self.jenkins_url)
        ]
        for cmd in commands:
            self.ssh_manager.execute_command(cmd)
        print("Jenkins agent installed.")

    def start_agent(self, agent_name, agent_secret):
        cmd = (
            "nohup java -jar agent.jar "
            "-jnlpUrl {}/computer/{}/jenkins-agent.jnlp "
            "-secret {} "
            "-workDir /home/ubuntu/agent > agent.log 2>&1 &"
        ).format(self.jenkins_url, agent_name, agent_secret)
        self.ssh_manager.execute_command(cmd)
        print("Jenkins agent started.")
