import requests
import time
import paramiko
import os
import socket
import sys
import json
import jenkins


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

    def wait_for_vm_running(self, server_id, timeout=300, interval=10):
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
            
            
    def delete_dns_record(self, domain):
        zone_name = 'comquent.academy'
        url = "https://dns.hetzner.com/api/v1/records"
        headers = {
            "Auth-API-Token": self.dns_api_token
        }

        zone_id = self.get_zone_id(zone_name)
        if not zone_id:
            print("Zone ID not found.")
            return

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            for record in records:
                if record["zone_id"] == zone_id and record["name"] == domain.split('.')[0]:
                    record_id = record["id"]
                    delete_url = f"{url}/{record_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    if delete_response.status_code == 200:
                        print("DNS record deleted successfully")
                    else:
                        print("Failed to delete DNS record", delete_response.status_code)
                        print(delete_response.json())
                        return
            print("DNS record not found.")
        else:
            print("Failed to retrieve DNS records", response.status_code)
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
            f"git clone --branch jenkins-jcac {repo_url} /var/jenkins_home/jenkins-jcac")

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

class JenkinsJobManager:
    def __init__(self, jenkins_url, user, password):
        try: 
            self.server = jenkins.Jenkins(jenkins_url, username=user, password=password)
            self.server.get_whoami()
            self.server.get_version()
            print(f"Connected to Jenkins server {jenkins_url}")
        except jenkins.JenkinsException as e:
            print(f"Failed to connect to Jenkins: {e}")
            sys.exit(1)
            
    def trigger_job(self, job_name):
        try:
            self.server.build_job(job_name)
            print(f"Triggered job {job_name}")
            return True
        except jenkins.JenkinsException as e:
            print(f"Failed to trigger job {job_name}: {e}")
            sys.exit(1)
            
    
    def get_last_build_number(self, job_name):
        try:
            job_info = self.server.get_job_info(job_name)
            return job_info['lastBuild']['number']
        except jenkins.JenkinsException as e:
            print(f"Failed to get last build number for job {job_name}: {e}")
            
            
    def get_build_status(self, job_name, build_number):
        try:
            build_info = self.server.get_build_info(job_name, build_number)
            if build_info['building']:
                return "BUILDING"
            else:
                return build_info['result']
        except jenkins.JenkinsException as e:
            print(f"Failed to get build status for job {job_name} build {build_number}: {e}")
            return sys.exit(1) 
        
    
    def wait_for_build_to_finish(self, job_name, timeout=300, interval=10):           
        build_number = self.get_last_build_number(job_name)
        if build_number is None:
            print(f"Failed to get last build number for job {job_name}")
            return sys.exit(1)
        
        print(f"Waiting for build {build_number} of job {job_name} to finish...")
        start_time = time.time()
        
        while True:
            status = self.get_build_status(job_name, build_number)
            if status == 'BUILDING':
                print("Build still in progress. Waiting...")
            elif status == 'SUCCESS':
                print("Build successful")
                return True
            elif status == 'FAILURE':
                print("Build failed")
                return sys.exit(1)
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print("Timeout waiting for build to finish")
                return 'TIMEOUT'
            
            time.sleep(interval)

class JenkinsTester:

    def __init__(self, ip_address, max_retries=10, wait_seconds=10):
        self.ip_address = ip_address
        self.max_retries = max_retries
        self.wait_seconds = wait_seconds

    def test_jenkins(self):
        url = f"http://{self.ip_address}:8080/login?from=%2F"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    print("Jenkins is up and running.")
                    return True
                else:
                    print(f"Attempt {attempt}: Jenkins is not running. Status code: {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"Attempt {attempt}: Failed to connect to Jenkins.")
            except requests.exceptions.Timeout:
                print(f"Attempt {attempt}: Connection to Jenkins timed out.")
            
            if attempt < self.max_retries:
                print(f"Waiting for {self.wait_seconds} seconds before retrying...")
                time.sleep(self.wait_seconds)
        
        print("Jenkins is not running after multiple attempts.")
        sys.exit(1) 


class NginxInstaller:

    def __init__(self, ssh_manager, domain):
        self.ssh_manager = ssh_manager
        self.domain = domain

    def install_nginx(self):
        if not self.ssh_manager.execute_command("DEBIAN_FRONTEND=noninteractive apt-get install nginx -y"):
            print("Failed to install Nginx")
            sys.exit(1)
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
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Port $server_port;
            }}
        }}
        """

        if not self.ssh_manager.execute_command(f"echo '{nginx_conf}' > /etc/nginx/sites-available/jenkins.conf"):
            print("Failed to create Nginx configuration file")
            return False
        print("Nginx configuration file created successfully")

        self.ssh_manager.execute_command("rm /etc/nginx/sites-enabled/default")

        self.ssh_manager.execute_command(
            "ln -s /etc/nginx/sites-available/jenkins.conf /etc/nginx/sites-enabled/jenkins.conf")

        print("Testing Nginx configuration...")
        if not self.ssh_manager.execute_command("nginx -t"):
            print("Nginx configuration test failed.")
            sys.exit(1)
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

    def __init__(self, vm_manager, ssh_key_path, jenkins_user, jenkins_pass, job_name):
        self.vm_manager = vm_manager
        self.ssh_key_path = ssh_key_path
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass
        self.vm_ip = None
        self.ssh_manager = None
        self.jenkins_url = None
        self.job_name = job_name
        self.jenkins_job_manager = None

    def wait_until_ready(self):
        server_id = self.vm_manager.vm['server']['id']
        print("Server ID:", server_id)
        if self.vm_manager.wait_for_vm_running(server_id):
            if not self.vm_ip:
                self.vm_ip = self.vm_manager.get_vm_ip()
            print(f"VM IP address: {self.vm_ip}")
            while not is_ssh_port_open(self.vm_ip):
                print(f"SSH port not open on {self.vm_ip}. Waiting...")
                time.sleep(10)
            print("VM is fully ready and reachable via SSH.")
            return True
        print("VM is not ready or failed to become reachable.")
        return False

    def setup_jenkins(self):
        self.ssh_manager = SSHManager(self.vm_ip, self.ssh_key_path)
        installer = JenkinsInstaller(self.ssh_manager, self.jenkins_user, self.jenkins_pass)
        installer.install_jenkins()
        
    def trigger_and_monitor_job(self):
        self.ip = self.vm_manager.get_vm_ip()
        self.jenkins_url = f"http://{self.ip}:8080"
        self.jenkins_job_manager = JenkinsJobManager(jenkins_url = self.jenkins_url, user = self.jenkins_user, password = self.jenkins_pass)

        success = self.jenkins_job_manager.trigger_job(self.job_name)
        if not success:
            print("Failed to trigger job")
            return sys.exit(1)

        result = self.jenkins_job_manager.wait_for_build_to_finish(self.job_name)
        
        if result == 'SUCCESS':
            print("Job completed successfully")
            return True
        elif result == 'FAILURE':
            print("Job failed")
            return sys.exit(1)
        else:
            print("Job ended with status: {result}")
            return sys.exit(1)
        
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
        

    def cleanup(self, delete_vm=True):
        if self.ssh_manager:
            self.ssh_manager.close()

        if delete_vm:
            self.vm_manager.delete_vm()

        if os.path.exists('vm_info.json'):
            os.remove('vm_info.json')

    def setup_nginx(self, domain):
        if not self.ssh_manager:
            self.ssh_manager = SSHManager(self.vm_ip, self.ssh_key_path)
        nginx_installer = NginxInstaller(self.ssh_manager, domain)
        nginx_installer.install_nginx()
        nginx_installer.obtain_ssl_certificate()
        nginx_installer.configure_nginx()


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'full'

    api_token = os.getenv('API_TOKEN')
    dns_api_token = os.getenv('DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key_path = os.getenv('SSH_PRIVATE_KEY_PATH')
    job_name = 'docker-test'

    os_type = "ubuntu-22.04"
    server_type = "cx22"
    ssh_key_id = 23404904

    manager = VMManager(api_token)
    env_manager = EnvironmentManager(manager, ssh_private_key_path, jenkins_user, jenkins_pass, job_name)

    if action == 'create':
        manager.create_vm(os_type, server_type, ssh_key_id)
        if env_manager.wait_until_ready():
            env_manager.setup_jenkins()
            success = env_manager.trigger_and_monitor_job()
            if success:
                print("Job completed successfully")
            else:
                print("Job failed")
                            
    elif action == 'create_dns':
        if dns_api_token:
            dns_manager = DNSManager(dns_api_token)
            ip_address = manager.get_vm_ip()
            dns_manager.create_dns_record(domain, ip_address)
        else:
            print("DNS_API_TOKEN not set")

    elif action == 'setup_nginx':
        if env_manager.wait_until_ready(): 
            env_manager.setup_nginx(domain)


    elif action == 'test':
        env_manager.test_jenkins()

    elif action == 'cleanup':
        env_manager.cleanup(delete_vm=False)
        dns_manager = DNSManager(dns_api_token)
        # dns_manager.delete_dns_record(domain)

    else:
        manager.create_vm(os_type, server_type, ssh_key_id)
        env_manager.setup_jenkins()
        env_manager.test_jenkins()
        env_manager.cleanup()


if __name__ == '__main__':
    main()
