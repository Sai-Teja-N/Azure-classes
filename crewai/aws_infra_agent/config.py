"""
Configuration for the AWS Infrastructure Scanner Agent.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ──────────── Load .env ────────────
# Try local .env first, then fallback to parallel_node_execution's .env
local_env = Path(__file__).parent / ".env"
fallback_env = Path(__file__).parent.parent.parent / "parallel_node_execution" / ".env"
load_dotenv(dotenv_path=local_env if local_env.exists() else fallback_env)

# ──────────── AWS Configuration ────────────
AWS_PROFILE = os.getenv("AWS_PROFILE", "rca-bedrock")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

# ──────────── Bedrock LLM Configuration ────────────
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.1"))
BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "4096"))
BEDROCK_REGION = os.getenv("BEDROCK_REGION", AWS_REGION)

# ──────────── Services to Scan ────────────
# Comma-separated list, e.g. "ec2,s3,rds,lambda,vpc,iam"
SCAN_SERVICES = os.getenv(
    "SCAN_SERVICES", "ec2,s3,rds,lambda,vpc,iam"
).lower().split(",")

# ──────────── Output Configuration ────────────
BASE_DIR = Path(__file__).parent
TERRAFORM_OUTPUT_DIR = BASE_DIR / "terraform_output"
TERRAFORM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────── Agent Verbosity ────────────
VERBOSE = os.getenv("CREW_VERBOSE", "true").lower() == "true"
