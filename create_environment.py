from jenkins_automation import VMManager, EnvironmentManager
import os

def main():
    api_token = "2qqLRyCJcWatOJuW46CQ0mvyaPxBkboh7fJxjSVrcsxEGVwAJDeR5RgO7vZ2PfwZ"
    os_type = "ubuntu-22.04"
    server_type = "cx22"
    ssh_key_id = 23404904
    ssh_private_key_path = os.path.expanduser("~/.ssh/id_rsa")
    
    manager = VMManager(api_token)
    manager.create_vm(os_type, server_type, ssh_key_id)
    
    env_manager = EnvironmentManager(manager, ssh_private_key_path)
    env_manager.setup_jenkins()
    
    
if __name__ == "__main__":
    main()
    