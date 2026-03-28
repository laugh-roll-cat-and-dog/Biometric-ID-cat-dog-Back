pipeline {
    agent any

    environment {
        REGISTRY = "192.168.1.57:5000"
        IMAGE = "whatthedog-back"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/laugh-roll-cat-and-dog/Biometric-ID-cat-dog-Back.git'
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker build -t $REGISTRY/$IMAGE:latest .'
            }
        }

        stage('Push Image') {
            steps {
                sh 'docker push $REGISTRY/$IMAGE:latest'
            }
        }

        stage('Deploy') {
            steps {
                sh 'KUBECONFIG=/var/jenkins_home/.kube/config kubectl apply -f deployment.yaml'
                sh 'KUBECONFIG=/var/jenkins_home/.kube/config kubectl delete pod -l app=whatthedog-back'
            }
        }
    }
}