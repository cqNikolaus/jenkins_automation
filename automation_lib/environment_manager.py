import os
import sys
import time
import socket
import jenkins
import yaml
from automation_lib import SSHManager, JenkinsInstaller, JenkinsJobManager, NginxInstaller, VMManager, JenkinsAgentInstaller





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
        self.installer = None
        
        
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
        self.installer = JenkinsInstaller(self.ssh_manager, self.jenkins_user, self.jenkins_pass, config_repo_url)
        self.installer.install_jenkins()
        print("Waiting for Jenkins to initialize...")
        time.sleep(40)
        self.installer.clone_config_repo_local()
        # Parse and retrieve agent definitions from the Jenkins YAML configuration files
        self.create_agent_vms(num_agents)
        
    def get_num_agents(self):
        agents = self.installer.parse_jenkins_yaml_files
        num_agents = len(agents)
        print(f"Number of agents specified in YAML file: {self.num_agents}")
        return num_agents
    
    def create_agents(self, os_type, server_type, ssh_key):
        self.num_agents = self.get_num_agents()
        agent_ips = []
        for i in range(self.num_agents):
            vm_name = f"agent-{i+1}-{int(time.time())}"
            agent_vm_info = self.vm_manager.create_vm("agent", os_type, server_type, ssh_key, vm_name=vm_name)
            if agent_vm_info is None:
                print(f"Agent VM {vm_name} could not be created")
                sys.exit(1)
            # Wait until agent vm is ready
            if not self.wait_until_ready("agent", index=i):    
                print(f"Agent VM {vm_name} not ready")
                sys.exit(1)
            agent_ip = self.vm_manager.get_vm_ip("agent", index=i)    
            if not agent_ip:
                print(f"Failed to retrieve Agent {i+1} IP adress ")
                sys.exit(1)
            agent_ips.append(agent_ip)    
        
        
        
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
            
            
                            
    def setup_agents(self):
        agent_count = len(self.vm_manager.agent_vms)
        for index in range(agent_count):
            agent_ip = self.vm_manager.get_vm_ip("agent", index=index)
            if not agent_ip:
                print(f"Could not retrieve IP for agent {index}")
                continue
            print(f"Setting up agent {index} at IP {agent_ip}")
            ssh_manager = SSHManager(agent_ip, self.key_file)
            agent_name = f"agent-{index + 1}"
            if index == 0:
                agent_label = 'build-node'
            else:
                agent_label = f"agent-label-{index + 1}"
            agent_installer = JenkinsAgentInstaller(ssh_manager)
            agent_installer.install_dependencies()
            
            

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