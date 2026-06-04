"""Node 2: Query SumoLogic for the source derived from the PD incident."""
import logging
import time
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import requests

from app.state import RCAState
from app.utils import cache
from app.config.settings import settings

log = logging.getLogger(__name__)


def _build_query(source: str, service: str) -> str:
    selector = source or service
    return (
        f'_sourceCategory="{selector}" '
        f'AND (ERROR OR Exception OR "5xx" OR timeout OR panic)'
        f'| fields _messagetime, _raw, _sourceHost | limit 200'
    )


def _run_sumo_job(query: str, frm: str, to: str) -> List[Dict[str, Any]]:
    auth = (settings.sumo_access_id, settings.sumo_access_key)
    base = settings.sumo_endpoint.rstrip("/")

    r = requests.post(
        f"{base}/search/jobs", auth=auth,
        json={"query": query, "from": frm, "to": to, "timeZone": "UTC"}, timeout=15,
    )
    if r.status_code in (401, 403):
        raise PermissionError(f"Sumo auth failed ({r.status_code}): {r.text[:200]}")
    r.raise_for_status()
    job_id = r.json()["id"]
    log.debug("Sumo job started: id=%s query='%s' from=%s to=%s", job_id, query, frm, to)
    
    for _ in range(30):
        s = requests.get(f"{base}/search/jobs/{job_id}", auth=auth, timeout=10).json()
        if s.get("state") in ("DONE GATHERING RESULTS", "DONE"):
            break
        if s.get("state") == "CANCELLED":
            raise RuntimeError("Sumo job cancelled")
        time.sleep(2)

    m = requests.get(
        f"{base}/search/jobs/{job_id}/messages", auth=auth,
        params={"offset": 0, "limit": 200}, timeout=15,
    ).json()
    return [msg.get("map", {}) for msg in m.get("messages", [])]


def sumo_fetcher(state: RCAState) -> RCAState:
    log.info("▶ node=sumo_fetcher")
    source   = state["sumo_source"]
    service  = state["service_name"]
    minutes  = state.get("time_range_minutes", 90)

    now = datetime.now(timezone.utc)
    
    # Format exactly as YYYY-MM-DDTHH:MM:SS.000Z
    frm = (now - timedelta(minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%S')
    to  = now.strftime('%Y-%m-%dT%H:%M:%S')
    
    query = _build_query(source, service)

    ckey = cache.cache_key("sumo", source, str(minutes))
    cached = cache.get(ckey)
    if cached:
        log.info("  cache hit for source=%s rows=%d", source, len(cached))
        results = cached
    else:
        if not settings.sumologic_enabled:
            local_path = settings.sumo_local_file_path
            log.info("  SUMOLOGIC_ENABLED is false. Reading from local file: %s", local_path)
            try:
                if not local_path or not os.path.exists(local_path):
                    log.warning("  Local file not found or empty path: '%s'", local_path)
                    results = []
                else:
                    with open(local_path, "r", encoding="utf-8") as f:
                        if local_path.endswith(".json"):
                            results = json.load(f)
                            if not isinstance(results, list):
                                results = [results]
                        else:
                            lines = f.read().splitlines()
                            results = [{"_raw": line} for line in lines if line.strip()]
                log.info("  loaded rows=%d from local file", len(results))
            except Exception as e:
                log.exception("  failed to read local file: %s", e)
                return {
                    **state, "sumo_query": query,
                    "sumo_results": [], "sumo_result_count": 0,
                    "errors": state.get("errors", []) + [f"local_file_read: {e}"],
                }
        else:
            try:
                results = _run_sumo_job(query, frm, to)
                cache.set(ckey, results, ttl=300)
                log.info("  fetched rows=%d from API", len(results))
            except PermissionError as e:
                log.warning("  sumo auth failed: %s", e)
                return {
                    **state, "sumo_query": query,
                    "sumo_results": [], "sumo_result_count": 0,
                    "errors": state.get("errors", []) + [f"sumo_fetch: {e}"],
                }
            except Exception as e:
                log.exception("  sumo fetch failed: %s", e)
                return {
                    **state, "sumo_query": query,
                    "sumo_results": [], "sumo_result_count": 0,
                    "errors": state.get("errors", []) + [f"sumo_fetch: {e}"],
                }
    
    log.debug("results=%d rows  query='%s' from=%s to=%s", len(results), query, frm, to)
    return {**state, "sumo_query": query, "sumo_results": results,
            "sumo_result_count": len(results)}
