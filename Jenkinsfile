pipeline {

    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        AWS_REGION     = 'ap-south-1'
        AWS_ACCOUNT_ID = '349036691344'
        REPO_NAME      = 'my-app'

        ECR_URI   = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE_TAG = "build-${BUILD_NUMBER}"

        DEPLOY_DIR = "/opt/flask-app"
    }

    stages {

        stage('Checkout Code') {
            steps {
                git credentialsId: 'github-credentials',
                    branch: 'main',
                    url: 'https://github.com/Sneha1016/Flask_MySQL_Dockerized_Login_System.git'
            }
        }

        stage('Create ECR Repository') {
            steps {
                withAWS(credentials: 'aws-credentials', region: AWS_REGION) {
                    sh '''
aws ecr describe-repositories \
  --repository-names ${REPO_NAME} \
  --region ${AWS_REGION} \
|| aws ecr create-repository \
  --repository-name ${REPO_NAME} \
  --region ${AWS_REGION}
'''
                }
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                withAWS(credentials: 'aws-credentials', region: AWS_REGION) {
                    sh '''
aws ecr get-login-password --region ${AWS_REGION} \
| docker login --username AWS --password-stdin ${ECR_URI}
'''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
cd demo
docker build -t ${REPO_NAME}:${IMAGE_TAG} .
docker tag ${REPO_NAME}:${IMAGE_TAG} ${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}
'''
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh '''
docker push ${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}
'''
            }
        }

        stage('Launch Flask EC2') {
            steps {
                withAWS(credentials: 'aws-credentials', region: AWS_REGION) {
                    script {

                        def ami = sh(
                            script: """
aws ssm get-parameter \
--name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
--region ${AWS_REGION} \
--query Parameter.Value \
--output text
""",
                            returnStdout: true
                        ).trim()

                        def instanceId = sh(
                            script: """
aws ec2 run-instances \
--image-id ${ami} \
--instance-type t3.micro \
--count 1 \
--key-name jenkins-flask \
--security-group-ids sg-053b498bb18d4d57a \
--tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Flask-App-EC2}]' \
--user-data file://user-data.sh \
--query 'Instances[0].InstanceId' \
--output text
""",
                            returnStdout: true
                        ).trim()

                        echo "Flask instance id = ${instanceId}"

                        sh "aws ec2 wait instance-running --instance-ids ${instanceId} --region ${AWS_REGION}"

                        def publicIp = sh(
                            script: """
aws ec2 describe-instances \
--instance-ids ${instanceId} \
--region ${AWS_REGION} \
--query 'Reservations[0].Instances[0].PublicIpAddress' \
--output text
""",
                            returnStdout: true
                        ).trim()

                        env.DEPLOY_HOST = "ec2-user@${publicIp}"
                        echo "Deploy host = ${env.DEPLOY_HOST}"
                    }
                }
            }
        }

        stage('Deploy on Flask EC2') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {

                    sh '''
ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} "

  echo 'Waiting for docker...'
  until command -v docker >/dev/null 2>&1; do sleep 5; done

  echo 'Waiting for aws...'
  until command -v aws >/dev/null 2>&1; do sleep 5; done

  sudo mkdir -p ${DEPLOY_DIR}
  sudo chown ec2-user:ec2-user ${DEPLOY_DIR}

  cd ${DEPLOY_DIR}

  export IMAGE_TAG=${IMAGE_TAG}
  export ECR_URI=${ECR_URI}

  aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_URI}

  docker compose pull
  docker compose up -d
"
'''
                }
            }
        }

    }

    post {
        success {
            echo "✅ Jenkins → ECR → Flask EC2 deployment completed"
        }
        failure {
            echo "❌ Pipeline failed"
        }
    }

}
