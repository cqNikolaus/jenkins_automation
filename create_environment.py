from jenkins_automation import VMManager, EnvironmentManager, DNSManager
import os

def main():
    api_token = os.getenv('API_TOKEN')
    dns_api_token = os.getenv('DNS_API_TOKEN')
    JENKINS_USER = credentials('JENKINS_USER')
    JENKINS_PASS = credentials('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key_path = os.getenv('SSH_PRIVATE_KEY_PATH')

    os_type = "ubuntu-22.04"
    server_type = "cx22"
    ssh_key_id = 23404904

    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key_id)
    
    env_manager = EnvironmentManager(manager, ssh_private_key_path)
    env_manager.setup_jenkins()
    
    dns_manager = DNSManager(dns_api_token)
    ip_adress = manager.get_vm_ip()
    dns_manager.create_dns_record(domain, ip_adress)
    
    env_manager.setup_nginx(domain)
    env_manager.cleanup(delete_vm=False)
    
    
if __name__ == "__main__":
    main()
    