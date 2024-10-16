import paramiko
from scp import SCPClient

class SSHManager:

    def __init__(self, ip_address, key_file):
        self.ip_address = ip_address
        self.key_file = key_file
        self.ssh = None


    def connect(self):
        if self.ssh is not None:
            return self.ssh
        print(f"Connecting to {self.ip_address}")
        try:
            key = paramiko.RSAKey.from_private_key(self.key_file)
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip_address, username='root', pkey=key)
            print("Connected successfully")
            return self.ssh
        except Exception as e:
            print(f"Failed to connect: {e}")
            return None

    def execute_command(self, command):
        try:
            ssh = self.connect()
            if ssh is None:
                return False
            stdin, stdout, stderr = ssh.exec_command(command)
            stdout_str = stdout.read().decode()
            stderr_str = stderr.read().decode()
            if stdout_str:
                print("Command executed successfully")
                print("Output:", stdout_str)
            if stderr_str:
                if "error" in stderr_str.lower():
                    print("Error:", stderr_str)
                else:
                    print("Standard error output (not necessarily an error):", stderr_str)
            return True
        except Exception as e:
            print(f"Failed to execute command: {e}")
            return False

    def close(self):
        if self.ssh:
            self.ssh.close()
            print("SSH connection closed")
            self.ssh = None

    def copy_file_to_vm(self, local_path, remote_path):
        try:
            if self.ssh is None:
                self.connect()
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.put(local_path, remote_path)
            print(f"Copied {local_path} to {remote_path} on the VM")
            return True
        except Exception as e:
            print(f"Failed to copy file: {e}")
            return False
