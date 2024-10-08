import requests
import time
import paramiko
import os
import socket
import sys
import json


class VMManager:

    def __init__(self, api_token):
        self.vm = None
        self.api_token = api_token

        if os.path.exists('vm_info.json'):
            with open('vm_info.json', 'r') as f:
                self.vm = json.load(f)

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
            with open('vm_info.json', 'w') as f:
                json.dump(self.vm, f)
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
        self.ssh = None

    def connect(self):
        if self.ssh is not None:
            return self.ssh
        print(f"Connecting to {self.ip_address} with {self.ssh_key_path}")
        try:
            key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip_address, username='root', pkey=key)
            print("Connected successfully")
            return self.ssh
        except Exception as e:
            print(f"Failed to connect: {e}")
            return None

    def execute_command(self, command, environment=None):
        try:
            ssh = self.connect()
            if ssh is None:
                return False
            stdin, stdout, stderr = ssh.exec_command(
                command, environment=environment)
            stdout_str = stdout.read().decode()
            stderr_str = stderr.read().decode()
            if stdout_str:
                print("Command executed successfully")
                print("Output:", stdout_str)
            if stderr_str:
                print("Error:", stderr_str)
            return True
        except Exception as e:
            print(f"Failed to execute command: {e}")
            return False

    def close(self):
        if self.ssh:
            self.ssh.close()
            print("SSH connection closed")
            self.ssh = None


class DNSManager:
    def __init__(self, dns_api_token):
        self.dns_api_token = dns_api_token

    def create_dns_record(self, domain, ip_address):
        zone_name = 'comquent.academy'
        url = "https://dns.hetzner.com/api/v1/records"
        headers = {
            "Auth-API-Token": self.dns_api_token,
            "Content-Type": "application/json"
        }

        zone_id = self.get_zone_id(zone_name)

        data = {
            "value": ip_address,
            "ttl": 3600,
            "type": "A",
            "name": domain.split('.')[0],  # Subdomain
            "zone_id": zone_id
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("DNS record created successfully")
        else:
            print("Failed to create DNS record", response.status_code)
            print(response.json())

    def get_zone_id(self, zone_name):
        url = "https://dns.hetzner.com/api/v1/zones"
        headers = {
            "Auth-API-Token": self.dns_api_token
        }
        response = requests.get(url, headers=headers)
        zones = response.json().get("zones", [])
        for zone in zones:
            if zone["name"] == zone_name:
                return zone["id"]
        print("Zone not found for zone name:", zone_name)
        return None


class JenkinsInstaller:

    def __init__(self, ssh_manager):
        self.ssh_manager = ssh_manager

    def install_jenkins(self):
        commands = [
            "DEBIAN_FRONTEND=noninteractive apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install openjdk-17-jdk -y",
            "curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null",
            "echo 'deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' | tee /etc/apt/sources.list.d/jenkins.list > /dev/null",
            "DEBIAN_FRONTEND=noninteractive apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install jenkins -y",
            "systemctl start jenkins",
            "systemctl enable jenkins"
        ]
        for command in commands:
            self.ssh_manager.execute_command(command)


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


class NginxInstaller:

    def __init__(self, ssh_manager, domain):
        self.ssh_manager = ssh_manager
        self.domain = domain

    def install_nginx(self):
        if not self.ssh_manager.execute_command("DEBIAN_FRONTEND=noninteractive apt-get install nginx -y"):
            print("Failed to install Nginx")
            return False
        print("Nginx installed successfully")
        return True

    def configure_nginx(self):
        nginx_conf = f"""
        server {{
            listen 80;
            server_name {self.domain};

            location / {{
                return 301 https://$host$request_uri;
            }}
        }}

        server {{
            listen 443 ssl;
            server_name {self.domain};

            ssl_certificate /etc/letsencrypt/live/{self.domain}/fullchain.pem;
            ssl_certificate_key /etc/letsencrypt/live/{self.domain}/privkey.pem;

            location / {{
                proxy_pass http://localhost:8080/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }}
        }}
        """

        if not self.ssh_manager.execute_command(f"echo '{nginx_conf}' > /etc/nginx/sites-available/jenkins.conf"):
            print("Failed to create Nginx configuration file")
            return False
        print("Nginx configuration file created successfully")

        self.ssh_manager.execute_command("rm /etc/nginx/sites-enabled/default")

        self.ssh_manager.execute_command("ln -s /etc/nginx/sites-available/jenkins.conf /etc/nginx/sites-enabled/jenkins.conf")
        
        print("Testing Nginx configuration...")
        if not self.ssh_manager.execute_command("nginx -t"):
            print("Nginx configuration test failed.")
            return False
        print("Nginx configuration test passed.")

        print("Restarting Nginx...")
        self.ssh_manager.execute_command("systemctl restart nginx")

    def obtain_ssl_certificate(self):
        # Certbot installieren
        self.ssh_manager.execute_command(
            "DEBIAN_FRONTEND=noninteractive apt-get install certbot python3-certbot-nginx -y")
        # SSL-Zertifikat beantragen
        result = self.ssh_manager.execute_command(
            f"certbot --nginx -d {self.domain} --non-interactive --agree-tos -m clemens.nikolaus@comquent.de")
        if not result:
            print("Failed to obtain SSL certificate")


def is_ssh_port_open(ip, port=22, timeout=5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        return result == 0


class EnvironmentManager:

    def __init__(self, vm_manager, ssh_key_path):
        self.vm_manager = vm_manager
        self.ssh_key_path = ssh_key_path
        self.vm_ip = None
        self.ssh_manager = None

    def setup_jenkins(self):
        server_id = self.vm_manager.vm['server']['id']
        if self.vm_manager.wait_for_vm(server_id):
            self.vm_ip = self.vm_manager.get_vm_ip()
            if self.vm_ip:
                print(f"VM IP address: {self.vm_ip}")
                # Warten, bis der SSH-Port offen ist
                while not is_ssh_port_open(self.vm_ip):
                    print(f"SSH port not open on {self.vm_ip}. Waiting...")
                    time.sleep(10)
                self.ssh_manager = SSHManager(self.vm_ip, self.ssh_key_path)

                installer = JenkinsInstaller(self.ssh_manager)
                installer.install_jenkins()

    def test_jenkins(self):
        if not self.vm_ip:
            self.vm_ip = self.vm_manager.get_vm_ip()
        if self.vm_ip:
            tester = JenkinsTester(self.vm_ip)
            if tester.test_jenkins():
                print("Jenkins test passed.")
                return True
            else:
                print("Jenkins test failed.")
                return False
        else:
            print("No VM IP address found.")
            return False

    def cleanup(self):
        if self.ssh_manager:
            self.ssh_manager.close()
        self.vm_manager.delete_vm()

        if os.path.exists('vm_info.json'):
            os.remove('vm_info.json')

    def setup_nginx(self, domain):
        # Stelle sicher, dass die VM-IP bekannt ist
        if not self.vm_ip:
            self.vm_ip = self.vm_manager.get_vm_ip()
            if not self.vm_ip:
                print("VM IP address not found. Cannot proceed with Nginx setup.")
                return

        # Stelle sicher, dass ssh_manager initialisiert ist
        if not self.ssh_manager:
            # Überprüfe, ob der SSH-Port offen ist
            while not is_ssh_port_open(self.vm_ip):
                print(f"SSH port not open on {self.vm_ip}. Waiting...")
                time.sleep(10)
            self.ssh_manager = SSHManager(self.vm_ip, self.ssh_key_path)

        nginx_installer = NginxInstaller(self.ssh_manager, domain)
        nginx_installer.install_nginx()
        nginx_installer.obtain_ssl_certificate()
        nginx_installer.configure_nginx()


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'full'

    api_token = os.getenv('API_TOKEN')
    dns_api_token = os.getenv('DNS_API_TOKEN')
    domain = os.getenv('DOMAIN')
    ssh_private_key_path = os.getenv('SSH_PRIVATE_KEY_PATH')

    os_type = "ubuntu-22.04"
    server_type = "cx22"
    ssh_key_id = 23404904

    manager = VMManager(api_token)
    env_manager = EnvironmentManager(manager, ssh_private_key_path)

    if action == 'create':
        manager.create_vm(os_type, server_type, ssh_key_id)
        env_manager.setup_jenkins()

    elif action == 'setup_nginx':
        env_manager.setup_nginx(domain)

    elif action == 'create_dns':
        if dns_api_token:
            dns_manager = DNSManager(dns_api_token)
            ip_address = manager.get_vm_ip()
            dns_manager.create_dns_record(domain, ip_address)
        else:
            print("DNS_API_TOKEN not set")

    elif action == 'test':
        env_manager.test_jenkins()

    elif action == 'cleanup':
        env_manager.cleanup()

    else:
        manager.create_vm(os_type, server_type, ssh_key_id)
        env_manager.setup_jenkins()
        env_manager.test_jenkins()
        env_manager.cleanup()


if __name__ == '__main__':
    main()
