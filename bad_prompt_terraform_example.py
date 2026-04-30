import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-01", 
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT") 
)

def generate_bad_terraform():
    response = client.chat.completions.create(
        model="your-gpt4-deployment-name", 
        messages=[
            # BAD SYSTEM MESSAGE: Too generic. Doesn't establish expertise or boundaries.
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            # BAD USER PROMPT: Vague. Lacks context, specific constraints, or formatting instructions.
            {
                "role": "user",
                "content": "Write some Terraform code for an EKS cluster."
            }
        ],
        # BAD PARAMETER: 0.8 is too high for writing strict code, increasing the chance 
        # of hallucinations or non-standard configurations.
        temperature=0.8
    )
    return response.choices[0].message.content

print(generate_bad_terraform())
