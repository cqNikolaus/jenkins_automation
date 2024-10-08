pipeline {
  agent {
    docker { 
      image 'python-build' 
      args '-u root:root'
    }
  }
  environment {
    API_TOKEN = credentials('HETZNER_API_TOKEN')
    DNS_API_TOKEN = credentials('HETZNER_DNS_API_TOKEN')
    DOMAIN = "jenkins-${env.BUILD_NUMBER}.comquent.academy" 
  }
  stages {
    stage('Create Jenkins Instance') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE')]) {
          sh '''
            set -e
            echo "create jenkins instance"
            chmod 600 $SSH_KEY_FILE
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            python jenkins_automation.py create
          '''
        }
      }
    }
    stage('Test Jenkins Installation') { 
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE')]) {
          sh '''
            set -e
            echo "check successful jenkins installation"
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            python jenkins_automation.py test
          '''
        }
      }
    }
    stage('Create DNS Record') {
      steps {
        sh '''
          set -e
          echo "create dns record"
          python jenkins_automation.py create_dns
        '''
      }
    }
    stage('Test DNS Record') {
      steps {
        sh '''
          set -e
          echo "test dns record"
          dig +short ${DOMAIN} @8.8.8.8
          if [ $? -ne 0 ]; then
            echo "DNS record does not exist or cannot be resolved."
            exit 1
          fi
        '''
      }
    }
    stage('Setup Nginx and SSL') { 
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE')]) {
          sh '''
            set -e
            echo "setup nginx and ssl"
            chmod 600 $SSH_KEY_FILE
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            python jenkins_automation.py setup_nginx
          '''
        }
      }
    }
    stage('Test SSL Certificate') {
      steps {
        sh '''
          set -e
          echo "test ssl certificate"
          echo | openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} 2>/dev/null | openssl x509 -noout -dates -subject
          if [ $? -ne 0 ]; then
            echo "SSL certificate is not valid or cannot be retrieved."
            exit 1
          fi
        '''
      }
    }
    stage('Shutdown Jenkins Instance') {
      steps {
        echo "kill jenkins"
        sh "python jenkins_automation.py cleanup"
      }
    }
  }
}
