pipeline {
  agent {
    docker { 
      image 'python-build' 
      args '-u root:root'
    }
  }
  environment {
    DOMAIN = "${params.DOMAIN}"
    ZONE_NAME = "comquent.academy" 
    SSH_KEY_NAME = 'clemens.nikolaus@comquent.de'
    JOB_NAME = 'docker-test'
    SSL_EMAIL = 'clemens.nikolaus@comquent.de'
    CONFIG_REPO = "${params.CONFIG_REPO}"
  }
  stages {
    stage('Checkout Workspace') {
      steps {
        git branch: 'main', url: 'https://github.com/cqNikolaus/jenkins_automation.git'
      }
    }
    stage('Create Jenkins Instance') {
      steps {
        withCredentials([
          sshUserPrivateKey(credentialsId: 'ssh-private-key', keyFileVariable: 'H_SSH_PRIVATE_KEY'),
          usernamePassword(credentialsId: 'jenkins-admin-credentials', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS'),
          string(credentialsId: 'hetzner-api-token', variable: 'H_API_TOKEN'),
          string(credentialsId: 'hetzner-dns-api-token', variable: 'H_DNS_API_TOKEN')
        ]) {
          script {
            def branchParam = params.BRANCH ?: ''
            def branchOption = branchParam ? "--branch ${branchParam}" : ""
            sh """
              set -e
              echo "create jenkins instance"
              pip install -e .
              python scripts/main.py create_jenkins --config-repo ${params.CONFIG_REPO} ${branchOption}
            """
          }
        }
      }
    }
    stage('Pipeline Test') { 
      steps {
        withCredentials([
          sshUserPrivateKey(credentialsId: 'ssh-private-key', keyFileVariable: 'H_SSH_PRIVATE_KEY'),
          usernamePassword(credentialsId: 'jenkins-admin-credentials', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS'),
          string(credentialsId: 'hetzner-api-token', variable: 'H_API_TOKEN'),
          string(credentialsId: 'hetzner-dns-api-token', variable: 'H_DNS_API_TOKEN')
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
        withCredentials([
          sshUserPrivateKey(credentialsId: 'ssh-private-key', keyFileVariable: 'H_SSH_PRIVATE_KEY'),
          usernamePassword(credentialsId: 'jenkins-admin-credentials', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS'),
          string(credentialsId: 'hetzner-api-token', variable: 'H_API_TOKEN'),
          string(credentialsId: 'hetzner-dns-api-token', variable: 'H_DNS_API_TOKEN')
        ]) {
          sh '''
            set -e
            echo "create dns record"
            python scripts/main.py create_dns 
          '''
        }
      }
    }
    stage('Test DNS Record') {
      steps {
        sh """
          set -e
          echo "test dns record"
          dig +short ${env.DOMAIN} @8.8.8.8
          if [ \$? -ne 0 ]; then
            echo "DNS record does not exist or cannot be resolved."
            exit 1
          fi
        """
      }
    }
    stage('Setup Nginx and SSL') { 
      steps {
        withCredentials([
          sshUserPrivateKey(credentialsId: 'ssh-private-key', keyFileVariable: 'H_SSH_PRIVATE_KEY'),
          usernamePassword(credentialsId: 'jenkins-admin-credentials', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS'),
          string(credentialsId: 'hetzner-api-token', variable: 'H_API_TOKEN'),
          string(credentialsId: 'hetzner-dns-api-token', variable: 'H_DNS_API_TOKEN')
        ]) {
          sh '''
            set -e
            echo "setup nginx and ssl"
            python scripts/main.py setup_nginx
          '''
        }
      }
    }
    stage('Test SSL Certificate') {
      steps {
        sh """
          set -e
          echo "test ssl certificate"
          sleep 10
          CERT_INFO=\$(echo | openssl s_client -connect ${env.DOMAIN}:443 -servername ${env.DOMAIN} -showcerts 2>/dev/null \\
          | sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' \\
          | openssl x509 -noout -dates -subject)
          if [ -z "\\\$CERT_INFO" ]; then
            echo "SSL certificate is not valid or cannot be retrieved."
            exit 1
          else
            echo "\\\$CERT_INFO"
          fi
        """
      }
    }
    stage('Shutdown Jenkins Instance') {
      steps {
        withCredentials([
          sshUserPrivateKey(credentialsId: 'ssh-private-key', keyFileVariable: 'H_SSH_PRIVATE_KEY'),
          usernamePassword(credentialsId: 'jenkins-admin-credentials', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_PASS'),
          string(credentialsId: 'hetzner-api-token', variable: 'H_API_TOKEN'),
          string(credentialsId: 'hetzner-dns-api-token', variable: 'H_DNS_API_TOKEN')
        ]) {
          echo "kill jenkins"
          sh "python scripts/main.py cleanup" 
        }
      }
    }
  }
}
