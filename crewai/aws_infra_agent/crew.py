from crewai import Crew, Process, Agent
from agents import create_scanner_agent, create_terraform_agent, create_advisor_agent
from tasks import create_scan_task, create_terraform_task, create_advisor_task
from llm import get_bedrock_llm
from config import VERBOSE

def create_infra_crew() -> Crew:
    # 1. Instantiate Agents
    scanner = create_scanner_agent()
    terraform = create_terraform_agent()
    advisor = create_advisor_agent()
    
    # 2. Instantiate Tasks
    scan_task = create_scan_task(scanner)
    tf_task = create_terraform_task(terraform)
    adv_task = create_advisor_task(advisor)
    
    # 3. Create Manager Agent
    manager_agent = Agent(
        role="Engineering Manager",
        goal="Coordinate the infrastructure audit and Terraform generation.",
        backstory="""You are the Engineering Manager overseeing the cloud infrastructure migration and audit. You ensure the Scanner, Terraform Engineer, and Solutions Architect deliver quality results.
        CRITICAL RULE: When reviewing data from the Scanner and passing it to the Terraform Engineer, you MUST preserve the exact resource IDs (e.g., vpc-1234abcd) and raw JSON structures. DO NOT summarize or omit any specific IDs.""",
        allow_delegation=True,
        llm=get_bedrock_llm(),
        verbose=VERBOSE
    )

    # 4. Assemble Crew
    crew = Crew(
        agents=[scanner, terraform, advisor],
        tasks=[scan_task, tf_task, adv_task],
        process=Process.hierarchical,
        manager_agent=manager_agent,
        verbose=VERBOSE,
        memory=False # Disabled to prevent OpenAI embedder errors
    )
    
    return crew
