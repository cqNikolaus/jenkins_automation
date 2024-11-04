import requests
import time
import os
import json

class VMManager:

    def __init__(self, api_token):
        self.controller_vm = None
        self.agent_vm = None
        self.api_token = api_token

        if os.path.exists('controller_vm_info.json'):
            with open('controller_vm_info.json', 'r') as f:
                self.controller_vm = json.load(f)
                
        if os.path.exists('agent_vm_info.json'):
            with open('agent_vm_info.json', 'r') as f:
                self.agent_vm = json.load(f)

    def create_vm(self, vm_type, os_type, server_type, ssh_key):
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
            if vm_type == "controller":
                self.controller_vm = response.json()
                print("Controller VM created successfully")
                with open('controller_vm_info.json', 'w') as f:
                    json.dump(self.controller_vm, f)
            if vm_type == "agent":
                self.agent_vm = response.json()
                print("Agent VM created successfully")
                with open('agent_vm_info.json', 'w') as f:
                    json.dump(self.agent_vm, f)
        else:
            print("Failed to create VM", response.status_code)
            print(response.json())
            
            
            

    def get_vm_ip(self, vm_type):
        if vm_type == "controller":
            return self.controller_vm["server"]["public_net"]["ipv4"]["ip"]
        elif vm_type == "agent":
            return self.agent_vm["server"]["public_net"]["ipv4"]["ip"]
            

    def delete_vms(self):
        for vm, vm_type in [(self.controller_vm, "controller"), (self.agent_vm, "agent")]:
            if vm:
                server_id = vm["server"]["id"]
                url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                }
                response = requests.delete(url, headers=headers)
                if response.status_code in [200, 202, 204]:
                    print(f" {vm_type} VM deleted successfully")
                    if vm_type == "controller":
                        self.controller_vm = None
                    else:
                        self.agent_vm = None
                else:
                    print(f"Failed to delete {vm_type} VM", response.status_code)
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