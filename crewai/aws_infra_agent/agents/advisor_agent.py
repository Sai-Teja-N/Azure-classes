from crewai import Agent
from llm import get_bedrock_llm
from config import VERBOSE
from tools.terraform_writer import write_terraform_file

def create_advisor_agent() -> Agent:
    return Agent(
        role="AWS Solutions Architect",
        goal="Analyze the AWS infrastructure and provide actionable recommendations for security, cost, and reliability.",
        backstory="""You are a Principal AWS Solutions Architect. You review infrastructure setups against the 
        AWS Well-Architected Framework. You identify security risks (like excessively permissive Security Groups or IAM roles), 
        cost optimization opportunities (like unused or oversized resources), and reliability improvements 
        (like single-AZ RDS deployments). You document these findings clearly.""",
        verbose=VERBOSE,
        allow_delegation=True, # Can delegate to Scanner to re-check things
        llm=get_bedrock_llm(),
        tools=[write_terraform_file] # For writing recommendations.md
    )
