#!/bin/bash
dnf update -y

dnf install docker -y
dnf install awscli -y

systemctl start docker
systemctl enable docker

usermod -aG docker ec2-user

curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
-o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose
