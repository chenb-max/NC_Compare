pipeline {
    agent any
    
    environment {
        PYTHON = 'python'  // Windows 用 'python'，Linux 用 'python3'
        PIP = 'pip'        // Windows 用 'pip'，Linux 用 'pip3'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm  // 从 SCM 检出代码
            }
        }
        
        stage('Setup Environment') {
            steps {
                bat "echo Setting up Python environment"  // Windows 用 bat
                // Linux 用 sh "echo Setting up Python environment"
                
                // 安装依赖
                bat "${PIP} install -r requirements.txt"
            }
        }
        
        stage('Run Script') {
            steps {
                // 执行 Python 主脚本
                bat "${PYTHON} src/main.py"
            }
        }
        
        stage('Run Tests') {
            steps {
                // 执行测试
                bat "${PYTHON} -m pytest tests/"
                
                // 生成测试报告（需要 pytest-html）
                bat "${PYTHON} -m pytest tests/ --html=test-report.html"
            }
            post {
                always {
                    // 归档测试报告
                    archiveArtifacts artifacts: 'test-report.html', fingerprint: true
                    
                    // 发布 JUnit 测试报告
                    junit '**/test-reports/*.xml'
                }
            }
        }
    }
    
    post {
        always {
            // 清理工作空间
            cleanWs()
            
            // 发送通知
            script {
                if (currentBuild.result == 'SUCCESS') {
                    echo '构建成功！🎉'
                } else {
                    echo '构建失败！❌'
                }
            }
        }
    }
}