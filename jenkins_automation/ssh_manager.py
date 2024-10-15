import paramiko

class SSHManager:

    def __init__(self, ip_address, ssh_key_path):
        self.ip_address = ip_address
        self.ssh_key_path = ssh_key_path
        self.ssh = None

    def connect(self):
        if self.ssh is not None:
            return self.ssh
        print(f"Connecting to {self.ip_address} with {self.ssh_key_path}")
        try:
            key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
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
                print("Error:", stderr_str)
            return True
        except Exception as e:
            print(f"Failed to execute command: {e}")
            return False

    def close(self):
        if self.ssh:
            self.ssh.close()
            print("SSH connection closed")
            self.ssh = None
