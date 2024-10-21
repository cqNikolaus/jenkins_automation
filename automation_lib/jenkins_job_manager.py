import jenkins
import sys
import time


class JenkinsJobManager:
    
    def __init__(self, jenkins_url, user, password):
        try: 
            print(f"Trying to connect to Jenkins server {jenkins_url}")
            print(f"User: {user}")
            print(f"Password: {password}")
            self.server = jenkins.Jenkins(jenkins_url, username=user, password=password)
            user_info = self.server.get_whoami()
            version = self.server.get_version()
            print(f"Connected to Jenkins {version} as {user_info['fullName']}")
        except jenkins.JenkinsException as e:
            print(f"Failed to connect to Jenkins: {e}")
            sys.exit(1)
            
            
    def trigger_job(self, job_name):
        try:
            self.server.build_job(job_name)
            print(f"Triggered job {job_name}")
            return True
        except jenkins.JenkinsException as e:
            print(f"Failed to trigger job {job_name}: {e}")
            raise

    
    def wait_for_build_to_finish(self, job_name, timeout=300, interval=2):
        start_time = time.time()
        
        # Warte darauf, dass der Job eine Build-Nummer erhält
        while time.time() - start_time < timeout:
            last_build_info = self.server.get_job_info(job_name)['lastBuild']
            if last_build_info is not None:
                self.build_number = last_build_info['number']
                break
            time.sleep(interval)
        else:
            print("Timeout beim Abrufen der Build-Nummer")
            return False        

        # Überwache den Build-Status
        while time.time() - start_time < timeout:
            last_build_info = self.server.get_job_info(job_name)['lastBuild']
            if last_build_info is not None:
                status = self.server.get_build_info(job_name, self.build_number)['result']
                if status == None:
                    print("Build still in progress. Waiting...")
                elif status == 'SUCCESS':
                    print("Build successful")
                    return 'SUCCESS'
                elif status == 'FAILURE':
                    print(f"Build failed")
                    return 'FAILURE'
                else:
                    print(f"Build ended with status: {status}")
                    return status
            time.sleep(interval)  

        print("Timeout waiting for build to finish")
        return False      