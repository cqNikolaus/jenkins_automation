from automation_lib import VMManager, DNSManager
from automation_lib.environment_manager import EnvironmentManager
import os
import sys
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description='Setup Jenkins environment and create DNS')
    parser.add_argument('--config-repo', help='The URL of the Jenkins configuration repository', required=True)
    parser.add_argument('--branch', help='The branch of the configuration repository to use', default=None)
    args = parser.parse_args()
    
    config_repo = args.config_repo
    branch = args.branch
    config_repo_url = f"--branch {branch} {config_repo}" if branch else config_repo
    
    
    api_token = os.getenv('H_API_TOKEN')
    dns_api_token = os.getenv('H_DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key = os.getenv('H_SSH_PRIVATE_KEY')
    zone_name = os.getenv('ZONE_NAME')
    ssh_key = os.getenv('SSH_KEY_NAME')
    job_name = os.getenv('JOB_NAME')
    


    os_type = "ubuntu-22.04"
    server_type = "cx22"

    vm_manager = VMManager(api_token)
    env_manager = EnvironmentManager(vm_manager, ssh_private_key, jenkins_user, jenkins_pass, job_name)
    vm_manager.create_vm("controller", os_type, server_type, ssh_key)
    
    # Reset agent_vms list and remove old agent_vms_info.json
    vm_manager.agent_vms = []
    if os.path.exists('agent_vms_info.json'):
        os.remove('agent_vms_info.json')
    
    num_agents = 3 # change to parameter on later updates
    for i in range(num_agents):
        agent_name = f"jenkins-agent-{i}-{int(time.time())}"
        agent_vm_info = vm_manager.create_vm("agent", os_type, server_type, ssh_key, vm_name=agent_name)
        if agent_vm_info is None:
            print(f"Agent VM {i} could not be created. Exiting.")
            sys.exit(1)
    
    
    try:
        if env_manager.wait_until_ready("controller"):
            for i in range(num_agents):
                if not env_manager.wait_until_ready("agent", index=i):
                    print(f"Agent VM {i} is not ready")
                    sys.exit(1)

            # Install Jenkins
            env_manager.setup_jenkins(config_repo_url)
            print("Jenkins installed")
            if env_manager.test_jenkins():
                    print("Jenkins is up and running")
            else:
                print("Jenkins is not running")
                sys.exit(1)
            
            
            # Set up agents
            if env_manager.initialize_jenkins_job_manager():
                env_manager.setup_agents()
            
            # Create Jenkins Job
            env_manager.trigger_and_monitor_job()

            # Create DNS record
            if dns_api_token and domain and zone_name:
                dns_manager = DNSManager(dns_api_token, zone_name)
                ip_address = vm_manager.get_vm_ip("controller")
                dns_manager.create_dns_record(domain, ip_address)
            else:
                print("DNS configuration missing")
                
            # Setup Nginx
            env_manager.setup_nginx(domain)
            print("Nginx set up")
            
            print("Environment successfully set up")
        else:
            print("Environment could not be set up")
            sys.exit(1)
    except Exception as e:
        print(f"Error setting up the environment: {e}")
        sys.exit(1)
        
        
if __name__ == "__main__":        
    main()
    