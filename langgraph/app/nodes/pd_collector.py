"""Node 1: Collect & normalize the PagerDuty incident payload."""
import logging
from datetime import datetime, timezone

from app.state import RCAState
from app.utils import cache

log = logging.getLogger(__name__)

SERVICE_TO_SUMO_SOURCE = {
    "checkout-api": "prod/checkout-api",
    "payments-svc": "prod/payments",
    "auth-gateway": "prod/auth",
    "orders-db":    "prod/db/orders",
}


def pd_collector(state: RCAState) -> RCAState:
    log.info("▶ node=pd_collector")
    payload  = state.get("pd_raw_payload") or {}
    incident = payload.get("incident") or payload

    incident_id = incident.get("id") or incident.get("incident_key") or "unknown"
    title       = incident.get("title") or incident.get("summary") or "No title"
    urgency     = incident.get("urgency", "high")
    created_at  = incident.get("created_at") or datetime.now(timezone.utc).isoformat()
    description = incident.get("description") or incident.get("details") or ""
    service     = (incident.get("service") or {}).get("summary") or \
                  incident.get("service_name", "unknown")
    

    sumo_source = SERVICE_TO_SUMO_SOURCE.get(service, f"prod/{service}")

    dedup_key = cache.cache_key("incident", incident_id)
    already = cache.get(dedup_key)
    cache.set(dedup_key, {"seen_at": datetime.now(timezone.utc).isoformat()}, ttl=600)

    log.info("  incident=%s service=%s → source=%s dedup=%s",
             incident_id, service, sumo_source, bool(already))
    return {
        **state,
        "incident_id": incident_id,
        "incident_title": title,
        "incident_urgency": urgency,
        "incident_created_at": created_at,
        "incident_description": description,
        "service_name": service,
        "sumo_source": sumo_source,
        "time_range_minutes": 30,
        "cache_hit": bool(already),
        "started_at": state.get("started_at") or datetime.now(timezone.utc).isoformat(),
        "errors": state.get("errors", []),
    }
