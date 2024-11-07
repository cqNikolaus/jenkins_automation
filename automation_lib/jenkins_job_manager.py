import jenkins
import sys
import time



class JenkinsJobManager:
    def __init__(self, jenkins_url, user, password):
        self.server = jenkins.Jenkins(
            jenkins_url,
            username=user,
            password=password
        )
        try:
            user_info = self.server.get_whoami()
            print(f"Erfolgreich mit Jenkins verbunden als {user_info['fullName']}")
        except jenkins.JenkinsException as e:
            print(f"Fehler beim Verbinden mit Jenkins: {e}")
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
    
    
    
    
    
    
    def create_agent_node(self, agent_name, label='linux'):
        try:
            # Create the agent node
            self.server.create_node(
                name=agent_name,
                nodeDescription='Automatically created agent',
                remoteFS='/home/ubuntu',
                labels=label,
                exclusive=False,
                launcher={'jnlp': True},
                numExecutors=2
            )
            print(f"Agent node {agent_name} created in Jenkins.")

            # Retrieve the agent secret
            agent_info = self.server.get_node_info(agent_name)
            agent_secret = agent_info['jnlpAgentSecret']
            return agent_secret
        except Exception as e:
            print(f"Failed to create agent node {agent_name}: {e}")
            return None
