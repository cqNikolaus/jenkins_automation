import sys
import argparse
import os
import json
from automation_lib import VMManager, EnvironmentManager, DNSManager




def main():
    parser = argparse.ArgumentParser(description='CI Pipeline: Validates the environment setup, tests the pipeline')
    parser.add_argument('command', choices=['create_jenkins', 'test_pipeline', 'create_dns', 'setup_nginx', 'cleanup'])
    parser.add_argument('--config-repo', help='https://github.com/cqNikolaus/jenkins_configs')
    
    args = parser.parse_args()
    
    if args.command == 'create_jenkins' and not args.config_repo:
        print("Error: --config-repo is required for create_jenkins")
        sys.exit(1)

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
    
    
    if args.command == 'create_jenkins':
        manager.create_vm(os_type, server_type, ssh_key_id)
        try:
            if env_manager.wait_until_ready():
                env_manager.setup_jenkins(config_repo_url=args.config_repo)
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
            dns_manager = DNSManager(dns_api_token, zone_name='comquent.academy')
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
        manager.create_vm(os_type, server_type, ssh_key_id)
        env_manager.setup_jenkins()
        env_manager.test_jenkins()
        env_manager.cleanup()


if __name__ == '__main__':
    main()
