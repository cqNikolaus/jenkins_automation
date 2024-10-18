import sys
import argparse
import os
import json
from automation_lib import VMManager, EnvironmentManager, DNSManager
from io import StringIO
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

    api_token = os.getenv('API_TOKEN')
    dns_api_token = os.getenv('DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key = os.getenv('SSH_PRIVATE_KEY')
    zone_name = os.getenv('ZONE_NAME')
    ssh_key = os.getenv('SSH_KEY_NAME')
    job_name = os.getenv('JOB_NAME')
    
    os_type = "ubuntu-22.04"
    server_type = "cx22"

    key_file = StringIO(ssh_private_key)
    manager = VMManager(api_token)
    env_manager = EnvironmentManager(manager, key_file, jenkins_user, jenkins_pass, job_name)
    
    
    if args.command == 'create_jenkins':
        manager.create_vm(os_type, server_type, ssh_key)
        try:
            if env_manager.wait_until_ready():
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
        if not manager.vm:
            if os.path.exists('vm_info.json'):
                with open('vm_info.json', 'r') as f:
                    manager.vm = json.load(f)     
                    
        env_manager.vm_ip = manager.get_vm_ip()
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
        if dns_api_token:
            dns_manager = DNSManager(dns_api_token, zone_name)
            ip_address = manager.get_vm_ip()
            dns_manager.create_dns_record(domain, ip_address)
        else:
            print("DNS_API_TOKEN not set")

    elif args.command == 'setup_nginx':
        if not manager.vm:
            if os.path.exists('vm_info.json'):
                with open('vm_info.json', 'r') as f:
                    manager.vm = json.load(f)
            else:
                print("vm_info.json not found. Cannot proceed with setup_nginx.")
                sys.exit(1)
        if env_manager.wait_until_ready(): 
            env_manager.setup_nginx(domain)


    elif args.command == 'cleanup':
        env_manager.cleanup(delete_vm=True)
        dns_manager = DNSManager(dns_api_token, zone_name='comquent.academy')
        dns_manager.delete_dns_record(domain)

    else:
        manager.create_vm(os_type, server_type, ssh_key)
        env_manager.setup_jenkins()
        env_manager.test_jenkins()
        env_manager.cleanup()


if __name__ == '__main__':
    main()
