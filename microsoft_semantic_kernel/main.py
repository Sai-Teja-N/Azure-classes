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
        
        import re
        # Clean up code block markers if the AI added them
        clean_code = terraform_code.replace("```terraform", "").replace("```hcl", "").replace("```", "").strip()
        
        # FORCIBLY scrub any hallucinated 'acl' attributes since LLMs are stubborn and it causes infinite hangs
        clean_code = re.sub(r'^\s*acl\s*=.*$', '', clean_code, flags=re.MULTILINE)
        
        # Save all the AI generated code into a single main.tf file
        with open(os.path.join(output_dir, "main.tf"), "w") as f:
            f.write(clean_code)
            
        print("\n[System] Saved Terraform code to output/main.tf")
        
        # Ensure provider.tf exists
        aws_region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
        provider_content = f"""terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
    tls = {{
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }}
  }}
}}

provider "aws" {{
  region = "{aws_region}"
}}
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
    2. Do NOT hardcode AMI IDs. ALWAYS use a `data "aws_ami"` block to dynamically fetch the latest AMI. You MUST include `owners = ["amazon"]` (for Amazon Linux) or `owners = ["099720109477"]` (for Ubuntu) inside the data block, otherwise it will fail with a 'query returned no results' error. For Amazon Linux 2023, the filter name should be `al2023-ami-2023.*-x86_64`.
    3. Ensure ALL resources and data sources referenced in your code are explicitly declared.
    4. For `tls_private_key`, the correct attribute for the private key is `private_key_pem`, NOT `private_key_pem_file`.
    5. Do NOT use `default = true` inside a `data "aws_subnet"` block, as it does not exist. If you need a subnet, use `data "aws_subnets" "default" { filter { name = "vpc-id" values = [data.aws_vpc.default.id] } }`. Better yet, do NOT specify a subnet or VPC for basic EC2 instances unless explicitly requested; AWS will automatically launch them in the default VPC and subnet.
    7. STRICT RULE: You MUST NOT use the `acl` attribute inside `aws_s3_bucket` under ANY circumstances. It is deprecated and forbidden. Use the `aws_s3_bucket_acl` resource instead if ACLs are needed, but generally avoid them. Likewise, do NOT use inline `versioning`, `server_side_encryption_configuration`, or `block_public_acls` inside `aws_s3_bucket`.
    8. For `aws_s3_bucket_logging`, `target_bucket` and `target_prefix` are top-level arguments. Do NOT nest them inside a `logging_enabled` block, as that block type does not exist in AWS Provider v5.
    9. For `aws_s3_bucket_lifecycle_configuration`, inside the `rule` block, you MUST use `status = "Enabled"` or `status = "Disabled"`. Do NOT use `enabled = true`, as it does not exist in v5.
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
