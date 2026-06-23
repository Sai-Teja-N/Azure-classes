pipeline {
    agent {
        docker {
            image 'python:3.10-slim'
            args '-u root' // Run as root to allow apt-get installations
        }
    }

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

        stage('Setup Dependencies') {
            steps {
                dir("${SK_DIR}") {
                    sh '''
                        echo "Installing OS dependencies and Terraform..."
                        apt-get update && apt-get install -y wget unzip git
                        
                        # Download and install Terraform
                        wget https://releases.hashicorp.com/terraform/1.8.5/terraform_1.8.5_linux_amd64.zip
                        unzip -o terraform_1.8.5_linux_amd64.zip
                        mv terraform /usr/local/bin/
                        terraform --version
                        
                        echo "Setting up Python environment..."
                        # We are already in python 3.10 container, but venv is still good practice
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
                    sh '''
                        . venv/bin/activate
                        echo "Running Semantic Kernel with prompt: ${INFRA_REQUEST}"
                        # AWS Credentials are automatically sourced from the Jenkins EC2 IAM Role
                        python3 main.py "${INFRA_REQUEST}"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution complete.'
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
