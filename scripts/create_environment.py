from automation_lib import VMManager, EnvironmentManager, DNSManager
import os
import sys
import argparse
from io import StringIO

def main():
    parser = argparse.ArgumentParser(description='Setup Jenkins environment and create DNS')
    parser.add_argument('--config-repo', help='The URL of the Jenkins configuration repository', required=True)
    args = parser.parse_args()
    
    api_token = os.getenv('API_TOKEN')
    dns_api_token = os.getenv('DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key = os.getenv('SSH_PRIVATE_KEY')
    zone_name = os.getenv('ZONE_NAME')
    ssh_key_id = int(os.getenv('SSH_KEY_ID'))

    job_name = 'docker-test'
    os_type = "ubuntu-22.04"
    server_type = "cx22"

    key_file = StringIO(ssh_private_key)
    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key_id)
    
    env_manager = EnvironmentManager(manager, key_file, jenkins_user, jenkins_pass, job_name)
    
    try:
        if env_manager.wait_until_ready():
            # Jenkins installieren
            env_manager.setup_jenkins(config_repo_url=args.config_repo)
            print("Jenkins installiert")
            
            # Initialen Job ausführen
            env_manager.initialize_jenkins_job_manager()
            env_manager.trigger_and_monitor_job()

            # DNS-Eintrag erstellen
            if dns_api_token and domain and zone_name:
                dns_manager = DNSManager(dns_api_token, zone_name)
                ip_address = manager.get_vm_ip()
                dns_manager.create_dns_record(domain, ip_address)
                print("DNS-Eintrag erstellt")
            else:
                print("DNS-Konfiguration fehlt")
                
            # Nginx einrichten
            env_manager.setup_nginx(domain)
            print("Nginx eingerichtet")
            
            print("Umgebung erfolgreich eingerichtet")
        else:
            print("Umgebung konnte nicht eingerichtet werden")
            sys.exit(1)
    except Exception as e:
        print(f"Fehler beim Aufsetzen der Umgebung: {e}")
        sys.exit(1)
            
if __name__ == "__main__":
    main()
    