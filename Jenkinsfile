pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        ansiColor('xterm')
    }

    environment {
        AWS_REGION     = 'ap-south-1'
        AWS_ACCOUNT_ID = '703671897854'
        REPO_NAME      = 'my-app'

        ECR_URI   = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE_TAG = "build-${BUILD_NUMBER}"

        CFT_DIR      = 'CFT'
        S3_BUCKET    = 'my-cloudformation-bucket11111'
        STACK_NAME   = 'parent-stack'
    }

    stages {

        stage('Checkout Code') {
            steps {
                git credentialsId: 'github-credentials',
                    branch: 'main',
                    url: 'https://github.com/Sneha1016/Flask_MySQL_Dockerized_Login_System.git'
            }
        }

        stage('Upload CloudFormation Templates to S3') {
            steps {
                withAWS(credentials: 'aws-credentials', region: AWS_REGION) {
                    sh """
                      aws s3 sync ${CFT_DIR} s3://${S3_BUCKET}/cloudformation --delete
                    """
                }
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                withAWS(credentials: 'aws-credentials', region: AWS_REGION) {
                    sh """
                      aws ecr get-login-password --region ${AWS_REGION} \
                      | docker login --username AWS --password-stdin ${ECR_URI}
                    """
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                  docker build -t ${REPO_NAME}:${IMAGE_TAG} .
                  docker tag ${REPO_NAME}:${IMAGE_TAG} ${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}
                """
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh """
                  docker push ${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}
                """
            }
        }

        stage('Deploy CloudFormation Stack') {
            steps {
                withAWS(credentials: 'aws-credentials', region: AWS_REGION) {
                    script {
                        def stackStatus = sh(
                            script: """
                              aws cloudformation describe-stacks \
                              --stack-name ${STACK_NAME} \
                              --query 'Stacks[0].StackStatus' \
                              --output text || echo NOT_FOUND
                            """,
                            returnStdout: true
                        ).trim()

                        if (stackStatus == "NOT_FOUND") {
                            echo "Creating CloudFormation stack..."
                            sh """
                              aws cloudformation create-stack \
                              --stack-name ${STACK_NAME} \
                              --template-url https://s3.${AWS_REGION}.amazonaws.com/${S3_BUCKET}/cloudformation/parent.yaml \
                              --capabilities CAPABILITY_NAMED_IAM
                            """
                            sh """
                              aws cloudformation wait stack-create-complete \
                              --stack-name ${STACK_NAME}
                            """
                        } else {
                            echo "Updating CloudFormation stack..."
                            sh """
                              aws cloudformation update-stack \
                              --stack-name ${STACK_NAME} \
                              --template-url https://s3.${AWS_REGION}.amazonaws.com/${S3_BUCKET}/cloudformation/parent.yaml \
                              --capabilities CAPABILITY_NAMED_IAM || echo "No changes"
                            """
                            sh """
                              aws cloudformation wait stack-update-complete \
                              --stack-name ${STACK_NAME}
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully"
            echo "Image pushed: ${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}"
        }

        failure {
            echo "❌ Pipeline failed"
        }

        cleanup {
            sh "docker system prune -f || true"
        }
    }
}
