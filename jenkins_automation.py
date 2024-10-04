import requests
import time
import paramiko
import os
import socket


class VMManager:

    def __init__(self, api_token):
        self.vm = None
        self.api_token = api_token

    def create_vm(self, os_type, server_type, ssh_key):
        url = "https://api.hetzner.cloud/v1/servers"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        data = {
            "name": f"jenkins-server-{int(time.time())}",
            "server_type": server_type,
            "image": os_type,
            "location": "nbg1",
            "start_after_create": True,
            "ssh_keys": [ssh_key]
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            self.vm = response.json()
            print("VM created successfully")
        else:
            print("Failed to create VM", response.status_code)
            print(response.json())

    def get_vm_ip(self):
        if self.vm:
            return self.vm["server"]["public_net"]["ipv4"]["ip"]
        return None

    def wait_for_vm(self, server_id, timeout=300, interval=10):
        url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
        }
        elapsed = 0
        while elapsed < timeout:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                server_status = response.json()['server']['status']
                if server_status == 'running':
                    print("Server is running.")
                    return True
                else:
                    print(f"Server status: {server_status}. Waiting...")
            else:
                print(f"Failed to get server status: {response.text}")
                return False
            time.sleep(interval)
            elapsed += interval
        print("Timeout waiting for server to be ready.")
        return False

    def delete_vm(self):
        if self.vm:
            server_id = self.vm["server"]["id"]
            url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
            }
            response = requests.delete(url, headers=headers)
            if response.status_code in [200, 202, 204]:
                print("VM deleted successfully")
                self.vm = None
            else:
                print("Failed to delete VM", response.status_code)
                print(response.json())
        else:
            print("No VM to delete")


class SSHManager:

    def __init__(self, ip_address, ssh_key_path):
        self.ip_address = ip_address
        self.ssh_key_path = ssh_key_path

    def connect(self):
        print(f"Connecting to {self.ip_address} with {self.ssh_key_path}")
        try:
            ssh_key_path_expanded = os.path.expanduser(self.ssh_key_path)
            key = paramiko.RSAKey.from_private_key_file(ssh_key_path_expanded)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip_address, username='root', pkey=key)
            print("Connected successfully")
            return ssh
        except Exception as e:
            print(f"Failed to connect: {e}")
            return None

    def execute_command(self, ssh, command, environment=None):
        try:
            stdin, stdout, stderr = ssh.exec_command(
                command, environment=environment)
            stdout_str = stdout.read().decode()
            stderr_str = stderr.read().decode()
            if stdout_str:
                print("Command executed successfully")
                print("Output:", stdout_str)
            if stderr_str:
                print("Error:", stderr_str)
        except Exception as e:
            print(f"Failed to execute command: {e}")


class JenkinsTester:

    def __init__(self, ip_address):
        self.ip_address = ip_address

    def test_jenkins(self):
        url = f"http://{self.ip_address}:8080/login?from=%2F"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                print("Jenkins is up and running.")
                return True
            else:
                print(f"Jenkins is not running. Status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Jenkins.")
            return False
        except requests.exceptions.Timeout:
            print("Connection to Jenkins timed out")
            return False


def is_ssh_port_open(ip, port=22, timeout=5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        return result == 0


def main():
    api_token = "2qqLRyCJcWatOJuW46CQ0mvyaPxBkboh7fJxjSVrcsxEGVwAJDeR5RgO7vZ2PfwZ"
    os_type = "ubuntu-22.04"
    server_type = "cx22"
    ssh_key_id = 23404904
    ssh_private_key_path = "~/.ssh/id_rsa"

    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key_id)

    server_id = manager.vm['server']['id']
    if manager.wait_for_vm(server_id):
        vm_ip = manager.get_vm_ip()
        if vm_ip:
            print(f"VM IP address: {vm_ip}")
            # Warten, bis der SSH-Port offen ist
            while not is_ssh_port_open(vm_ip):
                print(f"SSH port not open on {vm_ip}. Waiting...")
                time.sleep(10)
            ssh_manager = SSHManager(vm_ip, ssh_private_key_path)
            ssh = ssh_manager.connect()

            if ssh:
                # System aktualisieren
                ssh_manager.execute_command(
                    ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y")
                ssh_manager.execute_command(
                    ssh, "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y")

                # Java installieren
                ssh_manager.execute_command(
                    ssh, "DEBIAN_FRONTEND=noninteractive apt-get install openjdk-11-jdk -y")

                # Jenkins GPG-Schlüssel hinzufügen
                ssh_manager.execute_command(
                    ssh, "curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null")
                # Jenkins-Repository hinzufügen
                ssh_manager.execute_command(
                    ssh, "echo 'deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' | tee /etc/apt/sources.list.d/jenkins.list > /dev/null")

                # Paketliste aktualisieren
                ssh_manager.execute_command(
                    ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y")

                # Jenkins installieren
                ssh_manager.execute_command(
                    ssh, "DEBIAN_FRONTEND=noninteractive apt-get install jenkins -y")

                # Jenkins starten
                ssh_manager.execute_command(ssh, "systemctl start jenkins")
                ssh_manager.execute_command(ssh, "systemctl enable jenkins")

                ssh.close()

                tester = JenkinsTester(vm_ip)
                if tester.test_jenkins():
                    print("Jenkins test passed.")
                else:
                    print("Jenkins test failed.")

                manager.delete_vm()
        else:
            print("Failed to retrieve VM IP address")
    else:
        print("Server did not become ready in time.")


if __name__ == '__main__':
    main()
