import os
import sys
import time
import argparse

from automation_lib import VMManager, DNSManager
from automation_lib.environment_manager import EnvironmentManager

def main():
    """Set up Jenkins environments by creating VMs and configuring Jenkins instances."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Setup Jenkins environment')
    parser.add_argument('--config-repo', help='The URL of the Jenkins configuration repository', required=True)
    parser.add_argument('--branch', help='The branch of the configuration repository to use', default=None)
    args = parser.parse_args()
    
    # Prepare configuration repository URL
    config_repo = args.config_repo
    branch = args.branch
    config_repo_url = f"--branch {branch} {config_repo}" if branch else config_repo
    
    # Load environment variables
    api_token = os.getenv('H_API_TOKEN')
    dns_api_token = os.getenv('H_DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    subdomain = os.getenv('SUBDOMAIN')
    zone_name = os.getenv('ZONE_NAME')
    ssh_private_key = os.getenv('H_SSH_PRIVATE_KEY')
    ssh_key = os.getenv('SSH_KEY_NAME')
    job_name = os.getenv('JOB_NAME')
    num_instances = int(os.getenv('NUM_INSTANCES', '1'))
    server_type = os.getenv('SERVER_TYPE')
    os_type = "ubuntu-22.04"
    
    # Initialize VMManager
    vm_manager = VMManager(api_token)
    
    # Loop to create Jenkins instances
    for instance_number in range(0, num_instances):
        domain = f"{subdomain}-{instance_number}.{zone_name}"
        print(f"Creating instance {instance_number}/{num_instances} for domain {domain}")
    
        # Initialize EnvironmentManager
        env_manager = EnvironmentManager(
            vm_manager=vm_manager,
            key_file=ssh_private_key,
            jenkins_user=jenkins_user,
            jenkins_pass=jenkins_pass,
            job_name=job_name,
            os_type=os_type,
            server_type=server_type,
            ssh_key=ssh_key
        )

        # Create Controller-VM with unique name 
        controller_name = f"jenkins-controller-{instance_number}-{int(time.time())}"
        vm_manager.create_vm(
            vm_type="controller",
            os_type=os_type,
            server_type=server_type,
            ssh_key=ssh_key,
            vm_name=controller_name
        )
        
        # Remove old agent info
        agent_info_file = 'agent_vms_info.json'
        if os.path.exists(agent_info_file):
            os.remove(agent_info_file)
        vm_manager.agent_vms = []
        

        # Wait for controller VM to be ready and configure Jenkins
        try:
                if not env_manager.wait_until_ready("controller"):
                    print(f"Controller-VM ist nicht bereit.")
                    sys.exit(1)

                # Setup Jenkins            
                print("Setting up Jenkins...")
                env_manager.setup_jenkins(config_repo_url)
                if env_manager.test_jenkins():
                        print("Jenkins is up and running")
                else:
                    print("Jenkins is not running")
                    sys.exit(1)
                    

<<<<<<< HEAD

                # Create Jenkins Job
                # env_manager.trigger_and_monitor_job()
>>>>>>>

                # Create DNS record
                if dns_api_token:
                    dns_manager = DNSManager(dns_api_token, zone_name)
                    ip_address = vm_manager.get_vm_ip("controller")
                    dns_manager.create_dns_record(domain, ip_address)
                else:
                    print("DNS configuration missing")
                    
                # Setup Nginx
                env_manager.setup_nginx(domain)
                print("Nginx setup completed")
                
                print(f"Environment successfully set up for {domain}")
                
        except Exception as e:
            print(f"Error setting up the environment for {domain}: {e}")
            sys.exit(1)
            
            
if __name__ == "__main__":        
    main()
    