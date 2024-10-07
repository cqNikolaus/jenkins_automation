pipeline {
  agent {
    docker { 
      image 'python-build' 
    }
  }
  environment {
    API_TOKEN = credentials('HETZNER_API_TOKEN')
    DNS_API_TOKEN = credentials('HETZNER_DNS_API_TOKEN')
    DOMAIN = 'jenkins-${env.BUILD_NUMBER}.comquent.academy'
  }
  stages {
    stage('Init Environment') {
      steps {
        sh 'python -V'
      }
    }
    stage('Create Jenkins Instance') {
      steps {
        echo "create jenkins"
        sh "python jenkins_automation.py create"
      }
    }
    stage('Check successful Installation') {
      steps {
        echo "test jenkins"
        sh "python jenkins_automation.py test"
      }
    }
    stage('Create DNS Record'){
      steps{
        echo "create dns record"
        sh "python jenkins_automation.py create_dns"
      }
    }
    stage('Setup Nginx and SSL') {
      steps {
        echo "setup nginx and ssl"
        sh "python jenkins_automation.py setup_nginx"
      }
    }
  }
}
