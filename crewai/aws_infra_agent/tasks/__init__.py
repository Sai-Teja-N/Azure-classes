"""Task definitions for the AWS Infrastructure Delegation Crew."""

from tasks.infra_tasks import (
    create_scan_task,
    create_terraform_task,
    create_advisor_task,
)

__all__ = [
    "create_scan_task",
    "create_terraform_task",
    "create_advisor_task",
]
