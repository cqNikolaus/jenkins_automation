from jenkins_automation import VMManager, EnvironmentManager, DNSManager
import os
import sys

def main():
    api_token = os.getenv('API_TOKEN')
    dns_api_token = os.getenv('DNS_API_TOKEN')
    jenkins_user = os.getenv('JENKINS_USER')
    jenkins_pass = os.getenv('JENKINS_PASS')
    domain = os.getenv('DOMAIN')
    ssh_private_key_path = os.getenv('SSH_PRIVATE_KEY_PATH')
    zone_name = os.getenv('ZONE_NAME')

    os_type = "ubuntu-22.04"
    server_type = "cx22"
    ssh_key_id = 23404904

    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key_id)
    
    env_manager = EnvironmentManager(manager, ssh_private_key_path, jenkins_user, jenkins_pass, job_name=None)
    
    try:
        if env_manager.wait_until_ready():
            # Jenkins installieren
            env_manager.setup_jenkins()
            print("Jenkins installiert")

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
    