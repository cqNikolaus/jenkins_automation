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
    ZONE_NAME = "comquent.academy" 
    SSH_KEY_ID = '23404904'
    
  }
  stages {
    stage('Create Jenkins Instance') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE'), 
        usernamePassword(credentialsId: 'JENKINS_ADMIN_CREDENTIALS', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS')
        ]) {
          sh '''
            set -e
            echo "create jenkins instance"
            chmod 600 $SSH_KEY_FILE
            export SSH_PRIVATE_KEY_PATH=$SSH_KEY_FILE
            pip install -e .
            python scripts/main.py create_jenkins --config-repo https://github.com/cqNikolaus/jenkins_configs.git
          '''
        }
      }
    }
    stage('Pipeline Test') { 
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'SSH_PRIVATE_KEY', keyFileVariable: 'SSH_KEY_FILE'),
        usernamePassword(credentialsId: 'JENKINS_ADMIN_CREDENTIALS', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS')
        ]) {
          sh '''
            set -e
            echo "check successful pipeline job"
            python scripts/main.py test_pipeline 
          '''
        }
      }
    }
    stage('Create DNS Record') {
      steps {
        sh '''
          set -e
          echo "create dns record"
          python scripts/main.py create_dns 
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
            python scripts/main.py setup_nginx
          '''
        }
      }
    }
    stage('Test SSL Certificate') {
      steps {
        sh '''
          set -e
          echo "test ssl certificate"
          CERT_INFO=$(echo | openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} 2>/dev/null | openssl x509 -noout -dates -subject)
          if [ -z "$CERT_INFO" ]; then
            echo "SSL certificate is not valid or cannot be retrieved."
            exit 1
          else
            echo "$CERT_INFO"
          fi
        '''
      }
    }
    stage('Shutdown Jenkins Instance') {
      steps {
        echo "kill jenkins"
        sh "python scripts/main.py cleanup" 
      }
    }
  }
}
