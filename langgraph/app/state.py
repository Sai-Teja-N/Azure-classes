"""Shared state passed between LangGraph nodes."""
from typing import TypedDict, Optional, List, Dict, Any


class RCAState(TypedDict, total=False):
    # Input from PagerDuty webhook
    incident_id: str
    incident_title: str
    incident_urgency: str
    incident_created_at: str
    incident_description: str
    service_name: str
    pd_raw_payload: Dict[str, Any]

    # Derived routing info
    sumo_source: str
    sumo_query: str
    time_range_minutes: int

    # Fetched logs
    sumo_results: List[Dict[str, Any]]
    sumo_result_count: int

    # LLM output
    rca_summary: str
    probable_root_cause: str
    suggested_actions: List[str]
    confidence: float

    # Slack delivery
    slack_channel: str
    slack_message_ts: Optional[str]
    slack_delivered: bool

    # Bookkeeping
    cache_hit: bool
    errors: List[str]
    started_at: str
    finished_at: Optional[str]
