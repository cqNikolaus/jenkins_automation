import requests
import time
import dns.resolver


class DNSManager:
    def __init__(self, dns_api_token, zone_name):
        self.dns_api_token = dns_api_token
        self.zone_name = zone_name





    def create_dns_record(self, domain, ip_address):
        url = "https://dns.hetzner.com/api/v1/records"
        subdomain = domain.split('.')[0]
        print(f"Creating DNS record for {domain} with {subdomain} ")
        headers = {
            "Auth-API-Token": self.dns_api_token,
            "Content-Type": "application/json"
        }

        zone_id = self.get_zone_id(self.zone_name)
        print(f"Zone ID: {zone_id}")


        data = {
            "value": ip_address,
            "ttl": 300,
            "type": "A",
            "name": subdomain,  # Subdomain
            "zone_id": zone_id
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            print("DNS record created successfully")
        else:
            print("Failed to create DNS record", response.status_code)
            print(response.json())
            
        if self.wait_for_dns_propagation(domain, ip_address):
            print("DNS propagation completed.")
        else:
            print("DNS propagation not successful.")

            
            
            
            
            
    def get_zone_id(self, zone_name):
        url = "https://dns.hetzner.com/api/v1/zones"
        headers = {
            "Auth-API-Token": self.dns_api_token
        }
        response = requests.get(url, headers=headers)
        zones = response.json().get("zones", [])
        for zone in zones:
            if zone["name"] == zone_name:
                return zone["id"]
        print("Zone not found for zone name:", zone_name)
        return None        
            
            
            
            
            
            
    def delete_dns_record(self, domain):
        url = "https://dns.hetzner.com/api/v1/records"
        headers = {
            "Auth-API-Token": self.dns_api_token
        }

        zone_id = self.get_zone_id(self.zone_name)
        if not zone_id:
            print("Zone ID not found.")
            return

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            for record in records:
                if record["zone_id"] == zone_id and record["name"] == domain.split('.')[0]:
                    record_id = record["id"]
                    delete_url = f"{url}/{record_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    if delete_response.status_code == 200:
                        print("DNS record deleted successfully")
                    else:
                        print("Failed to delete DNS record", delete_response.status_code)
                        print(delete_response.json())
                        return
            print("DNS record not found.")
        else:
            print("Failed to retrieve DNS records", response.status_code)
            print(response.json())    




def wait_for_dns_propagation(self, domain, expected_ip, timeout=300):
        start_time = time.time()
        resolver = dns.resolver.Resolver()
        while time.time() - start_time < timeout:
            try:
                answers = resolver.resolve(domain, 'A')
                for rdata in answers:
                    if rdata.to_text() == expected_ip:
                        print(f"DNS entry for {domain} successfully propagated.")
                        return True
            except Exception:
                pass
            print(f"Waiting for DNS propagation for {domain}...")
            time.sleep(10)
        print(f"Timeout while waiting for DNS propagation for {domain}.")
        return False
