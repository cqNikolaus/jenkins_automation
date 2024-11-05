import os
import sys
import time
import socket
import jenkins
from automation_lib import SSHManager, JenkinsInstaller, JenkinsJobManager, NginxInstaller, VMManager





def is_ssh_port_open(ip, port=22, timeout=5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        return result == 0




class EnvironmentManager:

    def __init__(self, vm_manager, key_file, jenkins_user, jenkins_pass, job_name):
        self.vm_manager = vm_manager
        self.key_file = key_file
        self.jenkins_user = jenkins_user
        self.jenkins_pass = jenkins_pass
        self.vm_ip = None
        self.ssh_manager = None
        self.jenkins_url = None
        self.job_name = job_name
        self.jenkins_job_manager = None
        self.controller_ip = None
        
        
    def wait_until_ready(self, vm_type, index=None, timeout=600):
        if vm_type == "controller":
            self.vm_ip = self.vm_manager.get_vm_ip("controller")
        elif vm_type == "agent":
            self.vm_ip = self.vm_manager.get_vm_ip("agent", index=index)
        else:
            print("Invalid vm_type")
            return False

        if self.vm_ip is None:
            print(f"Could not retrieve IP for {vm_type} VM.")
            return False

        print(f"VM IP address: {self.vm_ip}")
        if self.vm_manager.wait_for_vm_running(vm_type, index=index, timeout=timeout):
            while not is_ssh_port_open(self.vm_ip):
                print(f"SSH port not open on {self.vm_ip}. Waiting...")
                time.sleep(10)
            print("VM is fully ready and reachable via SSH.")
            return True
        else:
            print("VM is not ready or failed to become reachable.")
            return False



    def setup_jenkins(self, config_repo_url):
        self.controller_ip = self.vm_manager.get_vm_ip("controller")
        print(f"self controller ip: {self.controller_ip}")
        self.ssh_manager = SSHManager(self.controller_ip, self.key_file)
        installer = JenkinsInstaller(self.ssh_manager, self.jenkins_user, self.jenkins_pass, config_repo_url)
        installer.install_jenkins()
        print("Waiting for Jenkins to initialize...")
        time.sleep(30)
        

        
    def test_jenkins(self):
        self.controller_ip = self.vm_manager.get_vm_ip("controller")
        if not self.vm_ip:
            self.vm_ip = self.vm_manager.get_vm_ip("controller")
        if self.vm_ip:
            self.jenkins_url = f"http://{self.controller_ip}:8080"
            max_retries = 10
            wait_seconds = 10
            for attempt in range(1, max_retries + 1):
                try: 
                    self.jenkins_job_manager = JenkinsJobManager(self.jenkins_url, self.jenkins_user, self.jenkins_pass)
                    print("Jenkins is up and running")
                    return True
                except Exception as e:
                    print(f"Attempt {attempt}: Failed to connect to Jenkins: {e}")
                    if attempt < max_retries:
                        print(f"Waiting {wait_seconds} seconds before retrying...")
                        time.sleep(wait_seconds)
                    else:
                        print("Max retries reached. Jenkins is not running.")
                        return False
        else:
            print("No VM IP address found")
            return False
            
            
    def initialize_jenkins_job_manager(self):
        if not self.jenkins_job_manager:
            self.controller_ip = self.vm_manager.get_vm_ip("controller")
            self.jenkins_url = f"http://{self.controller_ip}:8080"
            try:
                self.jenkins_job_manager = JenkinsJobManager(jenkins_url = self.jenkins_url, user=self.jenkins_user, password=self.jenkins_pass)
                print("Initialized Jenkins job manager")
                return True
            except jenkins.JenkinsException as e:
                print(f"Failed to initialize Jenkins job manager: {e}")
                return False
        else:
            return True
            
    def trigger_and_monitor_job(self):
        if not self.jenkins_job_manager:
            print("Jenkins job manager not initialized")
            return False
        
        try:
            self.jenkins_job_manager.trigger_job(self.job_name)
        except Exception as e:
            print("Failed to trigger job {e}")
            sys.exit(1)
            
        result = self.jenkins_job_manager.wait_for_build_to_finish(self.job_name)
        
        if result == 'SUCCESS':
            print("Job completed successfully")
            return True
        elif result == 'FAILURE':
            print("Job failed")
            sys.exit(1)
        else:
            print(f"Job ended with status: {result}")
            sys.exit(1)        

    def cleanup(self, delete_vm=True):
        if self.ssh_manager:
            self.ssh_manager.close()

        if delete_vm:
            self.vm_manager.delete_vms()

        if os.path.exists('controller_vm_info.json'):
            os.remove('controller_vm_info.json')
            
        
        if os.path.exists('agent_vm_info.json'):
            os.remove('agent_vm_info.json')


    def setup_nginx(self, domain):
        if not self.ssh_manager:
            self.ssh_manager = SSHManager(self.vm_ip, self.key_file)
        nginx_installer = NginxInstaller(self.ssh_manager, domain)
        nginx_installer.install_nginx()
        nginx_installer.obtain_ssl_certificate()
        nginx_installer.configure_nginx()