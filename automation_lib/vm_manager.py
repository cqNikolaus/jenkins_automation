import requests
import time
import os
import json

class VMManager:

    def __init__(self, api_token):
        self.vm = None
        self.api_token = api_token

        if os.path.exists('vm_info.json'):
            with open('vm_info.json', 'r') as f:
                self.vm = json.load(f)

    def create_master_vm(self, os_type, server_type, ssh_key):
        url = "https://api.hetzner.cloud/v1/servers"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        data = {
            "name": f"jenkins-server-{int(time.time())}",
            "server_type": server_type,
            "image": os_type,
            "location": "nbg1",
            "start_after_create": True,
            "ssh_keys": [ssh_key]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            self.vm = response.json()
            print("VM created successfully")
            with open('vm_info.json', 'w') as f:
                json.dump(self.vm, f)
        else:
            print("Failed to create VM", response.status_code)
            print(response.json())

    def get_vm_ip(self):
        if self.vm:
            return self.vm["server"]["public_net"]["ipv4"]["ip"]
        return None

    def delete_vm(self):
        if self.vm:
            server_id = self.vm["server"]["id"]
            url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
            }
            response = requests.delete(url, headers=headers)
            if response.status_code in [200, 202, 204]:
                print("VM deleted successfully")
                self.vm = None
            else:
                print("Failed to delete VM", response.status_code)
                print(response.json())
        else:
            print("No VM to delete")

    def wait_for_vm_running(self, server_id, timeout=300, interval=10):
        url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
        }
        elapsed = 0
        while elapsed < timeout:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                server_status = response.json()['server']['status']
                if server_status == 'running':
                    print("Server is running.")
                    return True
                else:
                    print(f"Server status: {server_status}. Waiting...")
            else:
                print(f"Failed to get server status: {response.text}")
                return False
            time.sleep(interval)
            elapsed += interval
        print("Timeout waiting for server to be ready.")
        return False