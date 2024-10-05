node() {
  checkout scm
  sh "ls -lart"
  sh "docker build -t python-build ."
}
