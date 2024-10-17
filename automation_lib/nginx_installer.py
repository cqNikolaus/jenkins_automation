import sys
import os

class NginxInstaller:

    def __init__(self, ssh_manager, domain):
        self.ssh_manager = ssh_manager
        self.domain = domain
        self.ssl_email = os.getenv('SSL_EMAIL')

    def install_nginx(self):
        if not self.ssh_manager.execute_command("DEBIAN_FRONTEND=noninteractive apt-get install nginx -y"):
            print("Failed to install Nginx")
            sys.exit(1)
        print("Nginx installed successfully")
        return True

    def configure_nginx(self):
        nginx_conf = f"""
        server {{
            listen 80;
            server_name {self.domain};

            location / {{
                return 301 https://$host$request_uri;
            }}
        }}

        server {{
            listen 443 ssl;
            server_name {self.domain};

            ssl_certificate /etc/letsencrypt/live/{self.domain}/fullchain.pem;
            ssl_certificate_key /etc/letsencrypt/live/{self.domain}/privkey.pem;

            location / {{
                proxy_pass http://localhost:8080/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Port $server_port;
            }}
        }}
        """

        if not self.ssh_manager.execute_command(f"echo '{nginx_conf}' > /etc/nginx/sites-available/jenkins.conf"):
            print("Failed to create Nginx configuration file")
            return False
        print("Nginx configuration file created successfully")

        self.ssh_manager.execute_command("rm /etc/nginx/sites-enabled/default")

        self.ssh_manager.execute_command(
            "ln -s /etc/nginx/sites-available/jenkins.conf /etc/nginx/sites-enabled/jenkins.conf")

        print("Testing Nginx configuration...")
        if not self.ssh_manager.execute_command("nginx -t"):
            print("Nginx configuration test failed.")
            sys.exit(1)
        print("Nginx configuration test passed.")

        print("Restarting Nginx...")
        self.ssh_manager.execute_command("systemctl restart nginx")

    def obtain_ssl_certificate(self):
        # Certbot installieren
        self.ssh_manager.execute_command(
            "DEBIAN_FRONTEND=noninteractive apt-get install certbot python3-certbot-nginx -y")
        # SSL-Zertifikat beantragen
        result = self.ssh_manager.execute_command(
            f"certbot --nginx -d {self.domain} --non-interactive --agree-tos -m {self.ssl_email}")
        if not result:
            print("Failed to obtain SSL certificate")



    
