FROM jenkins/jenkins:lts

ENV DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen en_US.UTF-8

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt

COPY jenkins.yaml /var/jenkins_home/casc_configs/jenkins.yaml

ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs/jenkins.yaml
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Duser.language=en -Duser.country=US"

USER jenkins