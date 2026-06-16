"""
AWS Bedrock LLM initialization for CrewAI agents.
Uses the native CrewAI LLM class (which uses LiteLLM under the hood).
"""
import os
from crewai import LLM

from config import (
    AWS_PROFILE,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    BEDROCK_MODEL_ID,
    BEDROCK_TEMPERATURE,
    BEDROCK_MAX_TOKENS,
    BEDROCK_REGION,
)

def get_bedrock_llm() -> LLM:
    """
    Create and return a CrewAI LLM instance for Amazon Bedrock.
    """
    # Ensure LiteLLM picks up explicit keys first
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
        os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
        from config import AWS_SESSION_TOKEN
        if AWS_SESSION_TOKEN:
            os.environ["AWS_SESSION_TOKEN"] = AWS_SESSION_TOKEN
            
        # Ensure we don't accidentally force a non-existent profile
        if "AWS_PROFILE" in os.environ:
            del os.environ["AWS_PROFILE"]
    elif AWS_PROFILE:
        os.environ["AWS_PROFILE"] = AWS_PROFILE
        
    os.environ["AWS_DEFAULT_REGION"] = BEDROCK_REGION
    os.environ["AWS_REGION"] = BEDROCK_REGION

    # Bedrock models must be prefixed with "bedrock/" in LiteLLM
    model_str = f"bedrock/{BEDROCK_MODEL_ID}" if not BEDROCK_MODEL_ID.startswith("bedrock/") else BEDROCK_MODEL_ID

    llm = LLM(
        model=model_str,
        temperature=BEDROCK_TEMPERATURE,
        max_tokens=BEDROCK_MAX_TOKENS,
    )

    return llm
