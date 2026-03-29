pipeline {
    agent any

    environment {
        IMAGE = "192.168.1.57:5000/whatthedog-back"
        // Inject HF token from Jenkins credentials
        HF_TOKEN = credentials('HF_TOKEN')
    }

    stages {
        stage('Checkout Latest Code') {
            steps {
                // Ensures we always fetch the latest main branch
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [[$class: 'WipeWorkspace']], // clean old workspace
                    userRemoteConfigs: [[url: 'https://github.com/laugh-roll-cat-and-dog/Biometric-ID-cat-dog-Back.git']]
                ])
            }
        }

        stage('Build Image') {
            steps {
                // Pass HF token as build arg to Docker
                sh 'docker build --no-cache --build-arg HF_TOKEN=$HF_TOKEN -t $IMAGE:latest .'
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