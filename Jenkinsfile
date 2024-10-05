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
        sh "python create_environment.py"
      }
    }
    stage('Check successful Installation') {
      steps {
        echo "test jenkins"
      }
    }
    stage('Shutdown Jenkins Instance') {
      steps {
        echo "kill jenkins"
      }
    }
  }
}
