from automation_lib import VMManager, EnvironmentManager, DNSManager
import os
import sys
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
    server_type = "cpx11"

    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key)
    
    
    env_manager = EnvironmentManager(manager, ssh_private_key, jenkins_user, jenkins_pass, job_name)
    
    try:
        if env_manager.wait_until_ready():
            # Install Jenkins
            env_manager.setup_jenkins(config_repo_url)
            print("Jenkins installed")
            
            # Create Jenkins Job
            env_manager.initialize_jenkins_job_manager()
            env_manager.trigger_and_monitor_job()

            # Create DNS record
            if dns_api_token and domain and zone_name:
                dns_manager = DNSManager(dns_api_token, zone_name)
                ip_address = manager.get_vm_ip()
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
    