import os
import re
import asyncio
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.bedrock import BedrockChatCompletion, BedrockChatPromptExecutionSettings

async def main():
    load_dotenv()
    
    kernel = Kernel()

    model_id = os.getenv("BEDROCK_MODEL_ID", "apac.amazon.nova-pro-v1:0")
    service_id = "bedrock_chat"
    
    bedrock_chat = BedrockChatCompletion(
        model_id=model_id,
        service_id=service_id,
    )
    
    kernel.add_service(bedrock_chat)

    system_message = """
    You are an expert Cloud Architect and Terraform Developer.
    Take the user's infrastructure request and generate Terraform HCL code.
    Output ONLY the Terraform code within ```terraform markdown blocks.
    Include a comment at the top of the block with the filename, e.g., `# filename: main.tf`.
    """

    req_settings = BedrockChatPromptExecutionSettings(
        service_id=service_id,
        max_tokens=2000,
        temperature=0.1
    )

    user_input = "Create an S3 bucket named rca-langgraph-sample-bucket"
    print(f"\nProcessing request using model: {model_id}...")
    print(f"Request: {user_input}")
    
    prompt = f"{system_message}\n\nUser Request: {user_input}"
    
    result = await kernel.invoke_prompt(
        prompt=prompt,
        settings=req_settings
    )
    
    response_text = str(result)
    print("\nAgent Response:")
    print(response_text)
    
    # Manually parse the terraform blocks and save them
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    blocks = re.findall(r"```(?:terraform|hcl)?\n(.*?)\n```", response_text, re.DOTALL | re.IGNORECASE)
    for i, block in enumerate(blocks):
        # try to find filename
        filename_match = re.search(r"#\s*(?:filename|file):\s*(.+?\.tf)", block, re.IGNORECASE)
        filename = filename_match.group(1).strip() if filename_match else f"main_{i}.tf"
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(block.strip() + "\n")
        print(f"Saved {filename} to {filepath}")

if __name__ == "__main__":
    asyncio.run(main())
