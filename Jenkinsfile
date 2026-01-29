pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        ansiColor('xterm')
    }

    environment {
        AWS_REGION     = 'ap-south-1'
        AWS_ACCOUNT_ID = '349036691344'
        REPO_NAME      = 'my-app'

        ECR_URI   = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE_TAG = "build-${BUILD_NUMBER}"

        DEPLOY_HOST = "ec2-user@13.232.141.8"
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

        stage('Deploy on EC2 using Docker Compose') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh '''
                      ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} "
                        cd ${DEPLOY_DIR}
                        export IMAGE_TAG=${IMAGE_TAG}
                        export ECR_URI=${ECR_URI}
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
            echo "✅ Jenkins CI/CD pipeline completed successfully"
        }
        failure {
            echo "❌ Pipeline failed"
        }
    }
}
