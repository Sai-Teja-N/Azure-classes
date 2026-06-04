import boto3
from botocore.exceptions import ClientError

def call_bedrock():
    # Initialize the Bedrock Runtime client using your profile
    session = boto3.Session(profile_name="rca-bedrock")
    client = session.client("bedrock-runtime", region_name="us-east-1")
    
    # Swapped to the instantly accessible Amazon Nova Micro model
    model_id = "amazon.nova-micro-v1:0" 
    
    user_message = "Explain what Amazon Bedrock is in two simple sentences."
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]
    
    try:
        print(f"Sending request to {model_id}...")
        response = client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0.5,
                "topP": 0.9
            },
        )
        
        response_text = response["output"]["message"]["content"][0]["text"]
        print("\nModel Response:")
        print("-" * 40)
        print(response_text)
        
    except ClientError as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")

if __name__ == "__main__":
    call_bedrock()