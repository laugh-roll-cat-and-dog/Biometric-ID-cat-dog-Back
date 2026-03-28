pipeline {
    agent any

    environment {
        IMAGE = "100.97.74.126:5000/my-backend"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/laugh-roll-cat-and-dog/Biometric-ID-cat-dog-Back.git'
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker build -t $IMAGE:latest .'
            }
        }

        stage('Push Image') {
            steps {
                sh 'docker push $IMAGE:latest'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                export KUBECONFIG=/root/.kube/config
                kubectl apply -f deployment.yaml
                kubectl rollout restart deployment backend
                '''
            }
        }
    }
}