"""FastAPI app: PagerDuty webhooks → RCA graph."""
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException

from app.utils.logging_setup import setup_logging
setup_logging()   # must run before importing modules that log at import time

from app.graph import graph  # noqa: E402

log = logging.getLogger("rca.api")
app = FastAPI(title="RCA LangGraph Service", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/webhooks/pagerduty")
async def pd_webhook(req: Request):
    body = await req.json()

    # Support both PD v3 ({"event":{"data":{...}}}) and flattened/test payloads.
    event    = body.get("event", {})
    incident = event.get("data") or body.get("incident") or body

    thread_id = incident.get("id") or str(uuid.uuid4())
    log.info("↩ received PD webhook incident=%s", thread_id)

    try:
        final_state = graph.invoke(
            {"pd_raw_payload": {"incident": incident}},
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as e:
        log.exception("graph run failed")
        raise HTTPException(500, f"graph error: {e}")

    log.info("✅ finished incident=%s slack_delivered=%s errors=%d",
             final_state.get("incident_id"),
             final_state.get("slack_delivered"),
             len(final_state.get("errors", [])))
             
    import json
    state_to_print = dict(final_state)
    
    print("\n" + "="*60)
    print("🚀 PIPELINE EXECUTION COMPLETE - FULL TRACE")
    print("="*60)
    
    print("\n[1] INITIAL WEBHOOK (From Postman)")
    print("-" * 60)
    print(json.dumps(state_to_print.get("pd_raw_payload", {}), indent=2))
    
    print("\n[2] FETCHED LOGS (From SumoLogic/Local)")
    print("-" * 60)
    print(f"Source: {state_to_print.get('sumo_source')}")
    print(f"Query:  {state_to_print.get('sumo_query')}")
    logs = state_to_print.get("sumo_results", [])
    print(f"Count:  {len(logs)} rows")
    if logs:
        print("Sample (First 2 rows):")
        print(json.dumps(logs[:2], indent=2))
        if len(logs) > 2:
            print(f"... and {len(logs) - 2} more rows ...")
            
    print("\n[3] LLM ROOT CAUSE ANALYSIS")
    print("-" * 60)
    print(json.dumps({
        "rca_summary": state_to_print.get("rca_summary"),
        "probable_root_cause": state_to_print.get("probable_root_cause"),
        "suggested_actions": state_to_print.get("suggested_actions"),
        "confidence": state_to_print.get("confidence")
    }, indent=2))
    
    print("\n[4] FINAL RAW STATE (Truncated)")
    print("-" * 60)
    if "sumo_results" in state_to_print:
        state_to_print["sumo_results"] = f"[{len(logs)} rows omitted for brevity]"
    print(json.dumps(state_to_print, indent=2, default=str))
    print("="*60 + "\n")

    return {
        "incident_id":     final_state.get("incident_id"),
        "slack_delivered": final_state.get("slack_delivered"),
        "cache_hit":       final_state.get("cache_hit"),
        "rca_summary":     final_state.get("rca_summary"),
        "probable_root_cause": final_state.get("probable_root_cause"),
        "suggested_actions":   final_state.get("suggested_actions"),
        "confidence":          final_state.get("confidence"),
        "errors":          final_state.get("errors", []),
    }
