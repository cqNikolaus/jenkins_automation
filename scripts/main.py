import argparse
import sys
import os
import json

from automation_lib import VMManager, DNSManager
from automation_lib.environment_manager import EnvironmentManager

def main():
    """CI Pipeline: Validates the environment setup, tests the pipeline."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='CI Pipeline: Validates the environment setup')
    parser.add_argument('command', choices=['create_jenkins', 'test_pipeline', 'create_dns', 'setup_nginx', 'cleanup'])
    parser.add_argument('--config-repo', help='URL of the configuration repository', required=True)
    parser.add_argument('--branch', help='The branch of the configuration repository to use', default=None)
    args = parser.parse_args()
    
    if args.command == 'create_jenkins' and not args.config_repo:
        print("Error: --config-repo is required for create_jenkins")
        sys.exit(1)
    
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
    ssh_private_key = os.getenv('H_SSH_PRIVATE_KEY')
    zone_name = os.getenv('ZONE_NAME')
    ssh_key = os.getenv('SSH_KEY_NAME')
    job_name = os.getenv('JOB_NAME')
    server_type = os.getenv('SERVER_TYPE')
    os_type = "ubuntu-22.04"
    domain = f"{subdomain}.{zone_name}"
    
    # Initialize managers
    vm_manager = VMManager(api_token)
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
    
    if args.command == 'create_jenkins':
        # Create Controller-VM
        vm_manager.create_vm(
            vm_type="controller", 
            os_type=os_type, 
            server_type=server_type, 
            ssh_key=ssh_key
        )
        
        # Remove old agent info
        agent_info_file = 'agent_vms_info.json'
        if os.path.exists(agent_info_file):
            os.remove(agent_info_file)
        vm_manager.agent_vms = []
        
        try:
            if not env_manager.wait_until_ready("controller"):
                print("Controller VM is not ready.")
                sys.exit(1)

            # Setup Jenkins
            print("Setting up Jenkins...")
            env_manager.setup_jenkins(config_repo_url)
            if env_manager.test_jenkins():
                print("Jenkins is up and running")
            else:
                print("Jenkins is not running")
                sys.exit(1)
        except Exception as e:
            print(f"Failed to create Jenkins: {e}")
            sys.exit(1)

    elif args.command == 'test_pipeline':
        # Load controller VM info if not already loaded
        if not vm_manager.controller_vm:
            if os.path.exists('controller_vm_info.json'):
                with open('controller_vm_info.json', 'r') as f:
                    vm_manager.controller_vm = json.load(f)
            else:
                print("Controller VM info not found.")
                sys.exit(1)

        env_manager.vm_ip = vm_manager.get_vm_ip("controller")
        if not env_manager.vm_ip:
            print("Controller VM IP not found.")
            sys.exit(1)
            
            if env_manager.initialize_jenkins_job_manager():
                if env_manager.trigger_and_monitor_job():
                    print("Pipeline test successful")
                else:
                    print("Pipeline test failed")
                    sys.exit(1)
            else:
                print("Failed to initialize Jenkins job manager")
                sys.exit(1)
                    
    elif args.command == 'create_dns':
            dns_manager = DNSManager(dns_api_token, zone_name)
            ip_address = vm_manager.get_vm_ip("controller")
            dns_manager.create_dns_record(domain, ip_address)

    elif args.command == 'setup_nginx':
        # Load controller VM info if not already loaded
        if not vm_manager.controller_vm:
            if os.path.exists('controller_vm_info.json'):
                with open('controller_vm_info.json', 'r') as f:
                    vm_manager.controller_vm = json.load(f)
            else:
                print("controller_vm_info.json not found. Cannot proceed with setup_nginx.")
                sys.exit(1)
        if not env_manager.wait_until_ready("controller"): 
            print("Controller VM is not ready.")
            sys.exit(1)
            
            env_manager.setup_nginx(domain)
            print("Nginx setup completed")

    elif args.command == 'cleanup':
        env_manager.cleanup(delete_vm=True)
        dns_manager = DNSManager(dns_api_token, zone_name=zone_name)
        dns_manager.delete_dns_record(domain)



if __name__ == '__main__':
    main()
