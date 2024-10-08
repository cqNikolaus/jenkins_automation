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
    DOMAIN = 'jenkins-${env.BUILD_NUMBER}.comquent.academy'
  }
  stages {
    stage('Create Jenkins Instance') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE')]) {
          sh '''
            echo "create jenkins instance"
            chmod 600 $SSH_KEY_FILE
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            python jenkins_automation.py create
          '''
        }
      }
    }
    stage('Check Successful Installation') {
      withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE')]) {
        steps {
          sh '''
            echo "check successful installation"
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            python jenkins_automation.py test
          '''
        }
      }
    }
    stage('Create DNS Record') {
      steps {
        sh '''
          echo "create dns record"
          python jenkins_automation.py create_dns
        '''
      }
    }
    stage('Setup Nginx and SSL') {
      withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE')]) {
        steps {
          sh '''
            echo "setup nginx and ssl"
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            python jenkins_automation.py setup_nginx
          '''
        }
      }
    }
  }
}
