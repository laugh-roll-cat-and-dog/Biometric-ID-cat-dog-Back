pipeline {
    agent any

    environment {
        IMAGE = "192.168.1.57:5000/whatthedog-back"
    }

    stages {


        stage('Build Image') {
            steps {
                sh 'docker build --no-cache -t $IMAGE:latest .'
            }
        }

        stage('Push Image') {
            steps {
                sh 'docker push $IMAGE:latest'
            }
        }

        stage('Deploy') {
            steps {
                sh 'KUBECONFIG=/var/jenkins_home/.kube/config kubectl apply -f deployment.yaml'
                sh 'KUBECONFIG=/var/jenkins_home/.kube/config kubectl rollout restart deployment whatthedog-back'
            }
        }
    }
}