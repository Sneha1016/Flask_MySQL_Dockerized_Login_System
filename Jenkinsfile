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

        // ✅ YOUR EXISTING FLASK SERVER
        DEPLOY_HOST = "ec2-user@13.127.106.75"
        DEPLOY_DIR  = "/opt/flask-app"
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

        stage('Deploy on Flask EC2') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {

                    sh '''
ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} "

  set -e

  sudo mkdir -p ${DEPLOY_DIR}
  sudo chown ec2-user:ec2-user ${DEPLOY_DIR}

  if ! command -v docker >/dev/null 2>&1; then
    echo 'Docker not found'
    exit 1
  fi

  if ! command -v aws >/dev/null 2>&1; then
    echo 'AWS CLI not found'
    exit 1
  fi

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
            echo "✅ Jenkins → ECR → Flask server deployment completed"
        }
        failure {
            echo "❌ Pipeline failed"
        }
    }
}
