pipeline {
    agent any

    environment {
        // Define path to the Semantic Kernel directory
        SK_DIR = 'microsoft_semantic_kernel'
        
        // Ensure Terraform commands run non-interactively
        TF_IN_AUTOMATION = 'true'
    }

    parameters {
        string(name: 'INFRA_REQUEST', defaultValue: 'Create an S3 bucket named rca-langgraph-sample-bucket', description: 'The natural language prompt for the Semantic Kernel to build infrastructure')
        booleanParam(name: 'RUN_TERRAFORM', defaultValue: false, description: 'Check this to actually execute the AI generated Terraform against AWS')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                dir("${SK_DIR}") {
                    sh '''
                        echo "Setting up Python environment..."
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Syntax Check') {
            steps {
                dir("${SK_DIR}") {
                    sh '''
                        . venv/bin/activate
                        echo "Checking Python syntax..."
                        python3 -m py_compile main.py
                        python3 -m py_compile test_script.py
                    '''
                }
            }
        }

        stage('Run AI Semantic Kernel') {
            when {
                expression { params.RUN_TERRAFORM == true }
            }
            steps {
                dir("${SK_DIR}") {
                    withCredentials([
                        // In Jenkins, you must configure these Secret Texts in 'Manage Jenkins -> Credentials'
                        string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
                        string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY'),
                        string(credentialsId: 'bedrock-model-id', variable: 'BEDROCK_MODEL_ID') // optional
                    ]) {
                        sh '''
                            . venv/bin/activate
                            echo "Running Semantic Kernel with prompt: ${INFRA_REQUEST}"
                            python3 main.py "${INFRA_REQUEST}"
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution complete.'
            // Clean up workspace if necessary
            // cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
