import requests
import time


class VMManager:

    def __init__(self, api_token):
        self.vm = None
        self.api_token = api_token

    def create_vm(self, os_type, server_type, ssh_key):
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
        else:
            print("Failed to create VM", response.status_code)
            print(response.json())


def main():
    api_token = "2qqLRyCJcWatOJuW46CQ0mvyaPxBkboh7fJxjSVrcsxEGVwAJDeR5RgO7vZ2PfwZ"
    os_type = input("Enter the OS type: ")
    server_type = input("Enter the server type: ")
    ssh_key = input("Enter your SSH key: ")

    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key)


if __name__ == '__main__':
    main()
