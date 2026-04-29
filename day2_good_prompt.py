import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-01", 
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT") 
)

def generate_good_terraform():
    response = client.chat.completions.create(
        model="your-gpt4-deployment-name", 
        messages=[
            # GOOD SYSTEM MESSAGE: Defines the exact role, constraints, and output format.
            {
                "role": "system",
                "content": (
                    "You are an expert Forward Deployed Engineer specializing in AWS, "
                    "Kubernetes, and infrastructure-as-code. Your task is to generate "
                    "production-ready Terraform configurations. "
                    "CRITICAL RULES: "
                    "1. Output ONLY valid Terraform code. "
                    "2. Do not include markdown formatting like ```hcl or any conversational text. "
                    "3. Include inline comments explaining the purpose of each resource block."
                )
            },
            # GOOD USER PROMPT: Provides exact specifications, versions, and architectural needs.
            {
                "role": "user",
                "content": (
                    "Create a Terraform configuration for an EKS managed node group. "
                    "Requirements: "
                    "- Instance type: t3.medium "
                    "- Scaling config: desired_size=3, min_size=1, max_size=5 "
                    "- It must include the IAM role creation with the standard "
                    "AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, and "
                    "AmazonEC2ContainerRegistryReadOnly policies attached."
                )
            }
        ],
        # GOOD PARAMETER: 0.1 ensures the model prioritizes the most highly probable, 
        # syntactically correct code tokens without trying to be "creative."
        temperature=0.1
    )
    return response.choices[0].message.content

print(generate_good_terraform())
