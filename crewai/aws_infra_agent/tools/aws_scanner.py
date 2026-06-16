import json
import boto3
from botocore.exceptions import ClientError
from crewai.tools import tool
from config import AWS_REGION, AWS_PROFILE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

def get_boto_client(service_name):
    """Helper to get a boto3 client using explicit keys or the configured profile."""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_session_token=AWS_SESSION_TOKEN,
            region_name=AWS_REGION
        )
    elif AWS_PROFILE:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    else:
        session = boto3.Session(region_name=AWS_REGION)
        
    return session.client(service_name)

@tool("Scan EC2 Instances")
def scan_ec2_instances() -> str:
    """Scans the AWS account for EC2 instances and returns their details."""
    try:
        ec2 = get_boto_client("ec2")
        response = ec2.describe_instances()
        instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append({
                    "InstanceId": instance.get("InstanceId"),
                    "InstanceType": instance.get("InstanceType"),
                    "State": instance.get("State", {}).get("Name"),
                    "VpcId": instance.get("VpcId"),
                    "SubnetId": instance.get("SubnetId"),
                    "Tags": instance.get("Tags", []),
                    "SecurityGroups": [sg.get("GroupId") for sg in instance.get("SecurityGroups", [])]
                })
        return json.dumps(instances, indent=2)
    except ClientError as e:
        return f"Error scanning EC2: {e}"

@tool("Scan EBS Volumes")
def scan_ebs_volumes() -> str:
    """Scans the AWS account for EBS volumes."""
    try:
        ec2 = get_boto_client("ec2")
        response = ec2.describe_volumes()
        volumes = []
        for v in response.get("Volumes", []):
            volumes.append({
                "VolumeId": v.get("VolumeId"),
                "Size": v.get("Size"),
                "State": v.get("State"),
                "VolumeType": v.get("VolumeType"),
                "Encrypted": v.get("Encrypted"),
                "Attachments": [{"InstanceId": a.get("InstanceId"), "State": a.get("State")} for a in v.get("Attachments", [])]
            })
        return json.dumps(volumes, indent=2)
    except ClientError as e:
        return f"Error scanning EBS: {e}"

@tool("Scan S3 Buckets")
def scan_s3_buckets() -> str:
    """Scans the AWS account for S3 buckets and returns their names."""
    try:
        s3 = get_boto_client("s3")
        response = s3.list_buckets()
        buckets = [{"Name": b.get("Name"), "CreationDate": str(b.get("CreationDate"))} for b in response.get("Buckets", [])]
        return json.dumps(buckets, indent=2)
    except ClientError as e:
        return f"Error scanning S3: {e}"

@tool("Scan EFS File Systems")
def scan_efs_filesystems() -> str:
    """Scans the AWS account for Elastic File Systems (EFS)."""
    try:
        efs = get_boto_client("efs")
        response = efs.describe_file_systems()
        filesystems = []
        for fs in response.get("FileSystems", []):
            filesystems.append({
                "FileSystemId": fs.get("FileSystemId"),
                "CreationTime": str(fs.get("CreationTime")),
                "LifeCycleState": fs.get("LifeCycleState"),
                "NumberOfMountTargets": fs.get("NumberOfMountTargets"),
                "SizeInBytes": fs.get("SizeInBytes", {}).get("Value"),
                "Encrypted": fs.get("Encrypted")
            })
        return json.dumps(filesystems, indent=2)
    except ClientError as e:
        return f"Error scanning EFS: {e}"

@tool("Scan VPC, Security Groups, and NACLs")
def scan_vpc_and_security_groups() -> str:
    """Scans the AWS account for VPCs, Subnets, Security Groups, and NACLs."""
    try:
        ec2 = get_boto_client("ec2")
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
        subnets = ec2.describe_subnets().get("Subnets", [])
        sgs = ec2.describe_security_groups().get("SecurityGroups", [])
        nacls = ec2.describe_network_acls().get("NetworkAcls", [])
        
        result = {
            "VPCs": [{"VpcId": v.get("VpcId"), "CidrBlock": v.get("CidrBlock")} for v in vpcs],
            "Subnets": [{"SubnetId": s.get("SubnetId"), "VpcId": s.get("VpcId"), "CidrBlock": s.get("CidrBlock")} for s in subnets],
            "SecurityGroups": [{"GroupId": sg.get("GroupId"), "GroupName": sg.get("GroupName"), "VpcId": sg.get("VpcId")} for sg in sgs],
            "NACLs": [{"NetworkAclId": n.get("NetworkAclId"), "VpcId": n.get("VpcId"), "IsDefault": n.get("IsDefault")} for n in nacls]
        }
        return json.dumps(result, indent=2)
    except ClientError as e:
        return f"Error scanning VPC/SGs/NACLs: {e}"

@tool("Scan IAM Roles")
def scan_iam_roles() -> str:
    """Scans the AWS account for IAM roles."""
    try:
        iam = get_boto_client("iam")
        response = iam.list_roles()
        roles = []
        for r in response.get("Roles", []):
            roles.append({
                "RoleName": r.get("RoleName"),
                "Arn": r.get("Arn"),
                "Description": r.get("Description", "")
            })
        # Truncating to avoid huge context payloads if many roles exist.
        return json.dumps(roles[:50], indent=2) 
    except ClientError as e:
        return f"Error scanning IAM: {e}"
