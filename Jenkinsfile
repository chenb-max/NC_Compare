pipeline {
    agent any
    
    environment {
        PYTHON = 'python3'
        PIP = 'pip3'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python') {
    steps {
        sh """
            ${PYTHON} -m venv venv
            . venv/bin/activate
            ${PIP} install -r requirements.txt
        """
    }
}
        
        stage('Lint') {
            steps {
                sh "flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics"
                sh "flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics"
            }
        }
        
        stage('Test') {
    parallel {
        stage('Unit Tests') {
            steps {
                sh "pytest tests/unit --cov=src -v"
            }
        }
        stage('Integration Tests') {
            steps {
                sh "pytest tests/integration --cov=src -v"
            }
        }
    }
}
    }
    
    post {
        always {
            cleanWs()
        }
    }
}