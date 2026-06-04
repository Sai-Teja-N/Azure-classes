"""Node 3: LLM Analyzer.
"""
import json
import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.state import RCAState
from app.utils import cache
from app.llm.factory import build_llm

log = logging.getLogger(__name__)

SYSTEM = """You are an SRE assistant performing root cause analysis.
Given a PagerDuty incident and recent logs from SumoLogic, produce a concise RCA.
Respond as STRICT JSON with keys:
  rca_summary (string, 3-5 sentences),
  probable_root_cause (string, 1 sentence),
  suggested_actions (array of 3-5 short strings),
  confidence (float 0..1).
Do not wrap the JSON in backticks or prose."""

USER = """Incident:
  id: {incident_id}
  title: {title}
  service: {service}
  urgency: {urgency}

Incident Description/Details:
{description}

SumoLogic source: {source}
Log sample ({count} rows, truncated):
{logs}

Return JSON only."""


def llm_analyzer(state: RCAState) -> RCAState:
    log.info("▶ node=llm_analyzer")
    results = state.get("sumo_results", [])
    sample = results[:40]
    fp = cache.fingerprint_logs(sample)
    ckey = cache.cache_key("rca", state["incident_id"], fp)

    cached = cache.get(ckey)
    if cached:
        log.info("  cache hit for incident=%s", state["incident_id"])
        return {**state, **cached}

    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", USER)])
    try:
        chain = prompt | build_llm() | JsonOutputParser()
        out: Dict[str, Any] = chain.invoke({
            "incident_id": state["incident_id"],
            "title":       state["incident_title"],
            "service":     state["service_name"],
            "urgency":     state["incident_urgency"],
            "description": state.get("incident_description", "No description provided."),
            "source":      state["sumo_source"],
            "count":       len(sample),
            "logs":        json.dumps(sample, default=str)[:8000],
        })
    except Exception as e:
        log.exception("  llm analysis failed: %s", e)
        return {
            **state,
            "rca_summary": "LLM analysis failed.",
            "probable_root_cause": "unknown",
            "suggested_actions": ["Investigate manually"],
            "confidence": 0.0,
            "errors": state.get("errors", []) + [f"llm: {e}"],
        }

    payload = {
        "rca_summary":         out.get("rca_summary", ""),
        "probable_root_cause": out.get("probable_root_cause", ""),
        "suggested_actions":   out.get("suggested_actions", []),
        "confidence":          float(out.get("confidence", 0.5)),
    }
    cache.set(ckey, payload, ttl=1800)
    log.info("  rca confidence=%.2f actions=%d",
             payload["confidence"], len(payload["suggested_actions"]))
    return {**state, **payload}
