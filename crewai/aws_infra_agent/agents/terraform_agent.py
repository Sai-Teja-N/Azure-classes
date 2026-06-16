from crewai import Agent
from llm import get_bedrock_llm
from config import VERBOSE
from tools.terraform_writer import write_terraform_file, read_terraform_file

def create_terraform_agent() -> Agent:
    return Agent(
        role="Senior Terraform Engineer",
        goal="Generate production-quality Terraform HCL code and import blocks for discovered AWS resources.",
        backstory="""You are an expert DevOps engineer specializing in Infrastructure as Code (IaC) using Terraform.
        You take inventory of existing AWS resources and write the necessary Terraform code (main.tf, variables.tf) 
        to manage them. Most importantly, you generate the `import {}` blocks (imports.tf) needed to bring 
        existing, unmanaged resources into Terraform state.
        
        CRITICAL RULE: You MUST use the exact, real IDs found in the Scanner's inventory report (e.g. vpc-1234abcd, i-01234abcd). 
        DO NOT generate generic boilerplate code (e.g., "example-bucket-name", "ami-0c55b159cbfafe1f0"). 
        If a resource is listed in the inventory, you must write a specific import block and resource block for it.""",
        verbose=VERBOSE,
        allow_delegation=True, # Can delegate back to Scanner if needed
        llm=get_bedrock_llm(),
        tools=[
            write_terraform_file,
            read_terraform_file,
        ]
    )
