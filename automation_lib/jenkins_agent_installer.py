from automation_lib import SSHManager

class JenkinsAgentInstaller:
    def __init__(self, ssh_manager):
        self.ssh_manager = ssh_manager

    def install_dependencies(self):
        commands = [
            # Installiere Java 17
            "sudo apt-get update -y",
            "sudo apt-get install -y openjdk-17-jre-headless",
            # Installiere Docker
            "sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release",
            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg",
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] '
            'https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | '
            'sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
            "sudo apt-get update -y",
            "sudo apt-get install -y docker-ce docker-ce-cli containerd.io",
            # Füge den Benutzer zur Docker-Gruppe hinzu
            "sudo usermod -aG docker root",
            # Starte und aktiviere den Docker-Dienst
            "sudo systemctl start docker",
            "sudo systemctl enable docker",
            # Erstelle das .ssh-Verzeichnis und setze Berechtigungen
            "mkdir -p ~/.ssh",
            "chmod 700 ~/.ssh"
        ]
        for cmd in commands:
            self.ssh_manager.execute_command(cmd)
        print("Abhängigkeiten installiert und SSH-Verzeichnis vorbereitet.")


