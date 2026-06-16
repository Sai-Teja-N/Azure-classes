from crewai import Task
from agents import create_scanner_agent, create_terraform_agent, create_advisor_agent
from config import AWS_REGION

def create_scan_task(scanner_agent=None) -> Task:
    if not scanner_agent:
        scanner_agent = create_scanner_agent()
        
    return Task(
        description=f"""1. Use ALL your available scanning tools to discover resources in the AWS account (Region: {AWS_REGION}).
        2. Ensure you scan EC2, EBS, VPCs (including SGs and NACLs), S3, EFS, and IAM.
        3. Compile all the JSON outputs into a comprehensive, structured text report detailing the current infrastructure. 
        INCLUDE THE REGION ({AWS_REGION}) IN YOUR REPORT.
        4. If a scan tool returns an error, log it but proceed with the other scans.""",
        expected_output="A comprehensive, structured inventory report of all discovered AWS resources that MUST INCLUDE ALL EXACT RESOURCE IDs (e.g. vpc-1234abcd) and raw JSON data. Do NOT summarize or truncate the IDs.",
        agent=scanner_agent
    )

def create_terraform_task(terraform_agent=None) -> Task:
    if not terraform_agent:
        terraform_agent = create_terraform_agent()
        
    return Task(
        description="""1. Analyze the infrastructure inventory report provided by the Scanner.
        2. Generate complete Terraform code for these SPECIFIC resources found in the report. You must create:
           - provider.tf (defining the AWS provider and region)
           - main.tf (defining the resource blocks FOR EVERY ID FOUND)
           - variables.tf (extracting region and common tags)
           - imports.tf (containing the `import { to = ... id = ... }` blocks for EVERY existing resource found)
        3. Use the 'Write File' tool to save each of these files to disk. Do NOT write generic "example-bucket" code.
        4. Do NOT attempt to run `terraform apply` or `terraform plan`.""",
        expected_output="Confirmation that provider.tf, main.tf, variables.tf, and imports.tf have been successfully written to the terraform_output directory.",
        agent=terraform_agent
    )

def create_advisor_task(advisor_agent=None) -> Task:
    if not advisor_agent:
        advisor_agent = create_advisor_agent()
        
    return Task(
        description="""1. Review the infrastructure inventory report.
        2. Identify at least 3 potential improvements across Security, Cost, and Reliability.
        3. Format these suggestions as a professional Markdown document.
        4. Use the 'Write File' tool to save this document as 'recommendations.md'.
        5. Your final output should be a summary of the key findings.""",
        expected_output="A summary of the key architectural recommendations and confirmation that recommendations.md was saved.",
        agent=advisor_agent
    )
