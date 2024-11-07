from automation_lib import SSHManager

class JenkinsAgentInstaller:
    def __init__(self, ssh_manager):
        self.ssh_manager = ssh_manager

    def install_dependencies(self):
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y openjdk-17-jre-headless",
        ]
        for cmd in commands:
            self.ssh_manager.execute_command(cmd)
        print("Abhängigkeiten installiert und SSH-Verzeichnis vorbereitet.")


