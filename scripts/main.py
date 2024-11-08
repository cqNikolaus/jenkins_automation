import sys
import argparse
import os
import time
import json
from automation_lib import VMManager, DNSManager
from automation_lib.environment_manager import EnvironmentManager
from dotenv import load_dotenv




def main():
    parser = argparse.ArgumentParser(description='CI Pipeline: Validates the environment setup, tests the pipeline')
    parser.add_argument('command', choices=['create_jenkins', 'test_pipeline', 'create_dns', 'setup_nginx', 'cleanup'])
    parser.add_argument('--config-repo', help='URL of the configuration repository')
    parser.add_argument('--branch', help='The branch of the configuration repository to use', default=None)
    args = parser.parse_args()
    
    config_repo = args.config_repo
    branch = args.branch
    config_repo_url = f"--branch {branch} {config_repo}" if branch else config_repo
    
    if args.command == 'create_jenkins' and not args.config_repo:
        print("Error: --config-repo is required for create_jenkins")
        sys.exit(1)
        
        
    load_dotenv()

    api_token = os.getenv('H_API_TOKEN')
    dns_api_token = os.getenv('H_DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key = os.getenv('H_SSH_PRIVATE_KEY')
    zone_name = os.getenv('ZONE_NAME')
    ssh_key = os.getenv('SSH_KEY_NAME')
    job_name = os.getenv('JOB_NAME')
    num_agents = int(os.getenv('NUM_AGENTS'))
    
    
    os_type = "ubuntu-22.04"
    server_type = "cx22"

    vm_manager = VMManager(api_token)
    env_manager = EnvironmentManager(vm_manager, ssh_private_key, jenkins_user, jenkins_pass, job_name)
    
    if args.command == 'create_jenkins':
        vm_manager.create_vm("controller", os_type, server_type, ssh_key)
        
        # Reset agent_vms list and remove old agent_vms_info.json
        vm_manager.agent_vms = []
        if os.path.exists('agent_vms_info.json'):
            os.remove('agent_vms_info.json')
            

        for i in range(num_agents):
            agent_name = f"jenkins-agent-{i+1}-{int(time.time())}"
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
                env_manager.setup_jenkins(config_repo_url)
                if env_manager.test_jenkins():
                    print("Jenkins is up and running")
                else:
                    print("Jenkins is not running")
                    sys.exit(1)
        except Exception as e:
            print(f"Failed to create Jenkins: {e}")
            sys.exit(1)
            
        if env_manager.initialize_jenkins_job_manager():
            env_manager.setup_agents()
        else:
            print(f"Failed to setup agents")
            sys.exit(1)
                
                
                
                
    elif args.command == 'test_pipeline':
        if not vm_manager.controller_vm:
            if os.path.exists('controller_vm_info.json'):
                with open('controller_vm_info.json', 'r') as f:
                    vm_manager.controller_vm = json.load(f)

                    
        env_manager.vm_ip = vm_manager.get_vm_ip("controller")
        if env_manager.vm_ip:
            if env_manager.initialize_jenkins_job_manager():
                if env_manager.trigger_and_monitor_job():
                    print("Docker test successful")
                else:
                    print("Docker test failed")
                    sys.exit(1)
            else:
                print("Failed to initialize Jenkins job manager")
                sys.exit(1)
                    
                    
    elif args.command == 'create_dns':
            dns_manager = DNSManager(dns_api_token, zone_name)
            ip_address = vm_manager.get_vm_ip("controller")
            dns_manager.create_dns_record(domain, ip_address)

    elif args.command == 'setup_nginx':
        if not vm_manager.controller_vm:
            if os.path.exists('controller_vm_info.json'):
                with open('controller_vm_info.json', 'r') as f:
                    vm_manager.controller_vm = json.load(f)
            else:
                print("controller_vm_info.json not found. Cannot proceed with setup_nginx.")
                sys.exit(1)
        if env_manager.wait_until_ready("controller"): 
            env_manager.setup_nginx(domain)


    elif args.command == 'cleanup':
        env_manager.cleanup(delete_vm=True)
        dns_manager = DNSManager(dns_api_token, zone_name='comquent.academy')
        dns_manager.delete_dns_record(domain)



if __name__ == '__main__':
    main()
