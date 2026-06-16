from crewai import Agent
from llm import get_bedrock_llm
from config import VERBOSE
from tools.aws_scanner import (
    scan_ec2_instances,
    scan_ebs_volumes,
    scan_s3_buckets,
    scan_efs_filesystems,
    scan_vpc_and_security_groups,
    scan_iam_roles,
)

def create_scanner_agent() -> Agent:
    return Agent(
        role="Senior AWS Infrastructure Analyst",
        goal="Discover and catalog specific AWS resources: EC2, EBS, VPC/SG/NACL, S3, EFS, and IAM.",
        backstory="""You are a meticulous AWS Infrastructure Analyst with years of experience auditing cloud environments. 
        Your primary role is to use your scanning tools to discover existing AWS resources. You leave no stone unturned.
        You map out EC2 instances, EBS volumes, VPCs (with SGs and NACLs), S3 buckets, EFS file systems, and IAM roles.
        You take the raw data from your tools and organize it logically for other team members to process.""",
        verbose=VERBOSE,
        allow_delegation=False, # Leaf worker, doesn't delegate
        llm=get_bedrock_llm(),
        tools=[
            scan_ec2_instances,
            scan_ebs_volumes,
            scan_s3_buckets,
            scan_efs_filesystems,
            scan_vpc_and_security_groups,
            scan_iam_roles,
        ]
    )
