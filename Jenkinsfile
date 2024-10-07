pipeline {
  agent {
    docker { 
      image 'python-build' 
    }
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
  }
}
