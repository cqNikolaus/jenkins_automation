import requests
import time
import os
import json

class VMManager:

    def __init__(self, api_token):
        self.controller_vm = None
        self.agent_vms = []
        self.api_token = api_token

        if os.path.exists('controller_vm_info.json'):
            with open('controller_vm_info.json', 'r') as f:
                self.controller_vm = json.load(f)
                
        if os.path.exists('agent_vms_info.json'):
            with open('agent_vms_info.json', 'r') as f:
                self.agent_vms = json.load(f)

    def create_vm(self, vm_type, os_type, server_type, ssh_key, vm_name=None):
        url = "https://api.hetzner.cloud/v1/servers"
        timestamp = int(time.time())
        if vm_name is None:
            vm_name = f"jenkins-{vm_type}-server-{timestamp}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        data = {
            "name": vm_name,
            "server_type": server_type,
            "image": os_type,
            "location": "nbg1",
            "start_after_create": True,
            "ssh_keys": [ssh_key]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            vm_info = response.json()
            if vm_type == "controller":
                self.controller_vm = vm_info
                print("Controller VM created successfully")
                with open('controller_vm_info.json', 'w') as f:
                    json.dump(self.controller_vm, f)
            elif vm_type == "agent":
                self.agent_vms.append(vm_info)
                print(f"Agent VM {vm_name} created successfully")
                with open('agent_vms_info.json', 'w') as f:
                    json.dump(self.agent_vms, f)
            return vm_info  # Erfolg, VM-Info zurückgeben
        else:
            print(f"Failed to create {vm_type} VM", response.status_code)
            print(response.json())
            return None  # Fehler, None zurückgeben

            
            
            

    def get_vm_ip(self, vm_type, index=None):
        if vm_type == "controller":
            return self.controller_vm["server"]["public_net"]["ipv4"]["ip"]
        elif vm_type == "agent":
            if index is not None and 0 <= index < len(self.agent_vms):
                return self.agent_vms[index]["server"]["public_net"]["ipv4"]["ip"]
            else:
                print("Invalid agent index")
                return None
            

    def delete_vms(self):
        # Delete Controller VM
        if self.controller_vm:
            server_id = self.controller_vm["server"]["id"]
            url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
            }
            response = requests.delete(url, headers=headers)
            if response.status_code in [200, 202, 204]:
                print("Controller VM deleted successfully")
                self.controller_vm = None
                if os.path.exists('controller_vm_info.json'):
                    os.remove('controller_vm_info.json')
            else:
                print("Failed to delete Controller VM", response.status_code)
                print(response.json())
        else:
            print("No Controller VM to delete")
        # Delete Agent VMs
        if self.agent_vms:
            for vm_info in self.agent_vms:
                server_id = vm_info["server"]["id"]
                vm_name = vm_info["server"]["name"]
                url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                }
                response = requests.delete(url, headers=headers)
                if response.status_code in [200, 202, 204]:
                    print(f"Agent VM '{vm_name}' deleted successfully")
                else:
                    print(f"Failed to delete Agent VM '{vm_name}'", response.status_code)
                    print(response.json())
            # Reset agent_vms list after deletion
            self.agent_vms = []
            if os.path.exists('agent_vms_info.json'):
                os.remove('agent_vms_info.json')
        else:
            print("No Agent VMs to delete")

                

    def wait_for_vm_running(self, vm_type, index=None, timeout=300, interval=10):
        if vm_type == "controller":
            vm = self.controller_vm
        elif vm_type == "agent":
            if index is not None and 0 <= index < len(self.agent_vms):
                vm = self.agent_vms[index]
            else:
                print("Invalid agent index")
                return False
        else:
            print("Invalid vm_type")
            return False

        if vm is None:
            print(f"{vm_type.capitalize()} VM not available.")
            return False

        server_id = vm["server"]["id"]
        url = f"https://api.hetzner.cloud/v1/servers/{server_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
        }
        elapsed = 0
        while elapsed < timeout:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                server_status = response.json()['server']['status']
                print(f"Server status: {server_status}.")
                if server_status == 'running':
                    print(f"{vm_type} Server is running.")
                    return True
                else:
                    print(f"Server status: {server_status}. Waiting...")
            elif response.status_code == 404:
                print(f"Server with ID '{server_id}' not found. Possible deletion.")
                return False
            else:
                print(f"Failed to get server status: {response.text}")
                return False
            time.sleep(interval)
            elapsed += interval
        print("Timeout waiting for server to be ready.")
        return False

    