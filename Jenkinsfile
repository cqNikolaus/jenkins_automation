pipeline {
  agent {
    docker { 
      image 'python-build' 
    }
  }
  environment {
    API_TOKEN = credentials('HETZNER_API_TOKEN')
    DNS_API_TOKEN = credentials('HETZNER_DNS_API_TOKEN')
    DOMAIN = 'comquent.academy'
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
    stage('Shutdown Jenkins Instance') {
      steps {
        echo "kill jenkins"
        sh "python jenkins_automation.py cleanup"
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
