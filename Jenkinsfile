pipeline {
    agent any
    
    environment {
        DOCKER_HUB_CREDENTIALS = credentials('dockerhub-creds')
        DOCKER_IMAGE = 'nakulkrishnan/resume-parser'
        APP_SERVER = 'ubuntu@3.80.43.27'
        AWS_REGION = 'us-east-1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code from GitHub...'
                git branch: 'main',
                    url: 'https://github.com/nakulkrish/resume-parser-devops.git'
                echo '✅ Code checked out successfully'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo '🐳 Building Docker image...'
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                        docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest
                    """
                    echo '✅ Docker image built successfully'
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                script {
                    echo '🧪 Running unit tests...'
                    sh """
                        # Run tests inside Docker container
                        docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} \
                            pytest tests/ -v --tb=short
                    """
                    echo '✅ All tests passed'
                }
            }
        }
        
        stage('Test Docker Image') {
            steps {
                script {
                    echo '🧪 Testing Docker image...'
                    sh """
                        # Run container in detached mode
                        docker run --rm -d --name test-container -p 5001:5000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        
                        # Wait for container to start
                        echo 'Waiting for container to start...'
                        sleep 10
                        
                        # Test health endpoint
                        curl -f http://localhost:5001/ || exit 1
                        
                        # Stop test container
                        docker stop test-container
                    """
                    echo '✅ Docker image test passed'
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    echo '📤 Pushing image to Docker Hub...'
                    sh """
                        echo \$DOCKER_HUB_CREDENTIALS_PSW | docker login -u \$DOCKER_HUB_CREDENTIALS_USR --password-stdin
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest
                    """
                    echo '✅ Images pushed to Docker Hub'
                }
            }
        }
        
        stage('Deploy to AWS EC2') {
            steps {
                script {
                    echo '🚀 Deploying to AWS EC2...'
                    sshagent(['app-server-ssh']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ${APP_SERVER} '
                                # Pull latest image
                                docker pull ${DOCKER_IMAGE}:latest
                                
                                # Stop and remove old container
                                docker stop resume-parser || true
                                docker rm resume-parser || true
                                
                                # Run new container
                                docker run -d \
                                  --name resume-parser \
                                  --restart unless-stopped \
                                  -p 80:5000 \
                                  -v /home/ubuntu/uploads:/app/uploads \
                                  -e FLASK_ENV=production \
                                  --log-driver=awslogs \
                                  --log-opt awslogs-region=${AWS_REGION} \
                                  --log-opt awslogs-group=/aws/ec2/resume-parser \
                                  --log-opt awslogs-create-group=true \
                                  ${DOCKER_IMAGE}:latest
                                
                                # Verify container is running
                                echo "Waiting for container to start..."
                                sleep 5
                                docker ps | grep resume-parser
                            '
                        """
                    }
                    echo '✅ Deployment completed'
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    echo '🏥 Running post-deployment health check...'
                    sshagent(['app-server-ssh']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ${APP_SERVER} '
                                # Wait a bit for app to fully start
                                sleep 5
                                
                                # Check if container is running
                                docker ps | grep resume-parser
                                
                                # Test the application endpoint
                                curl -f http://localhost/ || exit 1
                            '
                        """
                    }
                    echo '✅ Health check passed - Application is running'
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                script {
                    echo '🧹 Cleaning up old Docker images...'
                    sh """
                        # Remove old images (keep last 3 builds)
                        docker images ${DOCKER_IMAGE} --format "{{.Tag}}" | grep -v latest | sort -rn | tail -n +4 | xargs -r -I {} docker rmi ${DOCKER_IMAGE}:{} || true
                    """
                    echo '✅ Cleanup completed'
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 ==============================================='
            echo '🎉 PIPELINE COMPLETED SUCCESSFULLY!'
            echo '🎉 ==============================================='
            echo "🌐 Application URL: http://YOUR_APP_SERVER_IP"
            echo "🐳 Docker Image: ${DOCKER_IMAGE}:${BUILD_NUMBER}"
            echo "📊 Build Number: ${BUILD_NUMBER}"
        }
        failure {
            echo '❌ ==============================================='
            echo '❌ PIPELINE FAILED!'
            echo '❌ ==============================================='
            echo 'Check the logs above for error details'
        }
        always {
            echo '🔒 Logging out from Docker Hub...'
            sh 'docker logout || true'
        }
    }
}