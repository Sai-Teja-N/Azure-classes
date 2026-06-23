import os
import sys
import asyncio
import subprocess
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.bedrock import BedrockChatCompletion, BedrockChatPromptExecutionSettings
from semantic_kernel.functions import kernel_function
from typing import Annotated

# --- Native Python Plugin ---
class TerraformDeploymentPlugin:
    @kernel_function(
        name="save_and_deploy_terraform",
        description="Saves Terraform code to a main.tf file in the output directory and deploys it using Terraform CLI."
    )
    def save_and_deploy_terraform(
        self, 
        terraform_code: Annotated[str, "The Terraform HCL code to save and deploy"]
    ) -> Annotated[str, "The result of the deployment process"]:
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean up code block markers if the AI added them
        clean_code = terraform_code.replace("```terraform", "").replace("```hcl", "").replace("```", "").strip()
        
        # Save all the AI generated code into a single main.tf file
        with open(os.path.join(output_dir, "main.tf"), "w") as f:
            f.write(clean_code)
            
        print("\n[System] Saved Terraform code to output/main.tf")
        
        # Ensure provider.tf exists
        provider_content = """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  # Credentials picked up automatically from environment variables
}
"""
        with open(os.path.join(output_dir, "provider.tf"), "w") as f:
            f.write(provider_content)
            
        # Run Terraform commands automatically
        print("\n[System] Initializing Terraform...")
        init_result = subprocess.run(["terraform", "init"], cwd=output_dir)
        if init_result.returncode != 0:
            print("[Error] Terraform init failed.")
            sys.exit(1)

        print("\n[System] Applying Terraform Configuration...")
        apply_result = subprocess.run(["terraform", "apply", "-auto-approve"], cwd=output_dir)
        if apply_result.returncode == 0:
            return "[Success] Infrastructure deployed successfully!"
        else:
            print("[Error] Terraform apply failed.")
            sys.exit(1)


async def main():
    load_dotenv()
    
    # Fallback for Jenkins if environment variables are stripped
    if "AWS_DEFAULT_REGION" not in os.environ:
        os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
    if "AWS_REGION" not in os.environ:
        os.environ["AWS_REGION"] = "ap-south-1"
    
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<Your infrastructure request>\"")
        sys.exit(1)
        
    user_input = sys.argv[1]
    
    kernel = Kernel()

    model_id = os.getenv("BEDROCK_MODEL_ID", "apac.amazon.nova-pro-v1:0")
    service_id = "bedrock_chat"
    
    bedrock_chat = BedrockChatCompletion(
        model_id=model_id,
        service_id=service_id,
    )
    kernel.add_service(bedrock_chat)

    req_settings = BedrockChatPromptExecutionSettings(
        service_id=service_id,
        max_tokens=2000,
        temperature=0.1
    )

    # --- 1. Define Semantic Plugin for Research ---
    research_prompt = """
    You are an expert Cloud Architect.
    Research the following AWS deployment topic: {{$request}}
    
    Provide a detailed explanation of the required AWS resources, step-by-step implementation plan, and best practices.
    Do NOT write Terraform code yet. Just provide the architecture and steps.
    """
    
    # --- 2. Define Semantic Plugin for Terraform Generation ---
    terraform_prompt = """
    You are an expert Terraform Developer.
    Based on the following research and implementation steps:
    {{$research_plan}}

    Generate the Terraform HCL code to deploy the infrastructure.
    Output ONLY the Terraform code within ```terraform markdown blocks.
    IMPORTANT: Do NOT include a `provider "aws"` block in your code. The provider is already configured globally.
    CRITICAL INSTRUCTIONS:
    1. If you need an SSH key pair or any other local files, DO NOT use the `file()` function with local paths like `~/.ssh/id_rsa.pub`. Instead, use the `tls_private_key` and `aws_key_pair` resources to generate and use a new key dynamically.
    2. Do NOT hardcode AMI IDs (e.g. ami-0c55b159cbfafe1f0) as they vary by region and may not exist. Instead, ALWAYS use a `data "aws_ami"` block to dynamically fetch the latest AMI for the required OS (e.g., Amazon Linux 2023 or Ubuntu).
    3. Ensure ALL resources and data sources referenced in your code are explicitly declared.
    4. For `tls_private_key`, the correct attribute for the private key is `private_key_pem`, NOT `private_key_pem_file`.
    5. Do NOT use `default = true` inside a `data "aws_subnet"` block, as it does not exist. If you need a subnet, use `data "aws_subnets" "default" { filter { name = "vpc-id" values = [data.aws_vpc.default.id] } }`. Better yet, do NOT specify a subnet or VPC for basic EC2 instances unless explicitly requested; AWS will automatically launch them in the default VPC and subnet.
    6. Ensure your code is self-contained, complete, and syntactically valid Terraform 0.14+ syntax.
    7. Do NOT use inline `acl`, `versioning`, `server_side_encryption_configuration`, or `block_public_acls` attributes inside the `aws_s3_bucket` block. These are deprecated in Terraform AWS Provider v5. You MUST use standalone resources like `aws_s3_bucket_public_access_block`, `aws_s3_bucket_versioning`, etc.
    """
    
    # Add Semantic Functions as Plugins
    research_function = kernel.add_function(
        plugin_name="AWSOpsPlugin",
        function_name="ResearchTopic",
        prompt=research_prompt,
        prompt_execution_settings=req_settings
    )
    
    terraform_function = kernel.add_function(
        plugin_name="AWSOpsPlugin",
        function_name="GenerateTerraform",
        prompt=terraform_prompt,
        prompt_execution_settings=req_settings
    )
    
    # --- 3. Add Native Python Plugin ---
    deploy_plugin = kernel.add_plugin(TerraformDeploymentPlugin(), plugin_name="DeployPlugin")
    
    print(f"\nProcessing request using model: {model_id}...")
    print(f"Request: {user_input}")
    
    # Pipeline Execution using Plugins
    print("\n--- Step 1: Researching AWS Topic ---")
    research_result = await kernel.invoke(research_function, request=user_input)
    print(str(research_result))
    
    print("\n--- Step 2: Generating Terraform Code ---")
    terraform_result = await kernel.invoke(terraform_function, research_plan=str(research_result))
    print(str(terraform_result))
    
    print("\n--- Step 3: Saving and Deploying Infrastructure ---")
    deploy_result = await kernel.invoke(deploy_plugin["save_and_deploy_terraform"], terraform_code=str(terraform_result))
    print(str(deploy_result))

if __name__ == "__main__":
    asyncio.run(main())
