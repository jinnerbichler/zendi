FROM jenkins/jenkins:lts
MAINTAINER j.innerbichler@gmail.com

USER root

# installing dependencies
RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -
RUN apt-get update && apt-get install -y maven wget nodejs && rm -rf /var/lib/apt/lists/*

# installing Docker
ENV DOCKER_VERSION 17.06.0-ce
RUN wget https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz &&\
	tar -xvf docker-${DOCKER_VERSION}.tgz &&\
	cp docker/docker* /usr/bin/ &&\
	chown jenkins:jenkins /usr/bin/docker*
