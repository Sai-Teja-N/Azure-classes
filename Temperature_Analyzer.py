import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()
# 1. Initialize the Azure OpenAI Client
# Unlike standard OpenAI, Azure requires your specific endpoint and API version.
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-12-01-preview",  # Check Azure docs for the latest API version
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT") 
)

def analyze_incident(log_data):
    try:
        # 2. Make the API Call
        response = client.chat.completions.create(
            # In Azure, you use the "Deployment Name" you chose in Azure AI Studio, 
            # not necessarily the base model name.
            model="gpt-4o", 
            
            # 3. Define the Messages Array
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert TechOps engineer. Your job is to analyze "
                        "infrastructure logs and provide a concise root cause analysis. "
                        "Do not guess. If there is not enough information, state that clearly. "
                        "Format your output with two headers: 'Root Cause' and 'Remediation'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Analyze this Kubernetes cluster event log: {log_data}"
                }
            ],
            
            # 4. Set Generation Parameters
            # Using a very low temperature (0.1) because incident triage requires 
            # factual precision, not creative writing.
            temperature=0.1, 
            
            # We explicitly leave top_p out to use the default (1.0), adhering 
            # to the best practice of only altering one parameter at a time.
            # top_p=1.0, 
            
            max_tokens=400
        )
        
        # 5. Extract and return the AI's response
        return response.choices[0].message.content

    except Exception as e:
        return f"An error occurred: {e}"

# Example Usage
if __name__ == "__main__":
    sample_log = "Warning: FailedScheduling: 0/5 nodes are available: 2 node(s) had untolerated taint, 3 Insufficient memory."
    
    print("Sending request to Azure OpenAI...\n")
    analysis = analyze_incident(sample_log)
    print(analysis)
