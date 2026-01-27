pipeline {
    agent any

    stages {

        stage('Checkout Code') {
            steps {
                echo 'Code already checked out'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                  docker build -t flask-login-app -f demo/Dockerfile demo
                '''
            }
        }

        stage('Run Containers') {
            steps {
                sh '''
                  cd demo
                  docker-compose down || true
                  docker-compose up -d
                '''
            }
        }
    }
}
