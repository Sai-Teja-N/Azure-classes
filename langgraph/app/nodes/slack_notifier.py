"""Node 4: Post the RCA summary to Slack.

If SLACK_DRY_RUN=true (or no bot token is configured), logs the formatted
message instead of calling Slack — useful for local testing.
"""
import logging
from datetime import datetime, timezone

import requests

from app.state import RCAState
from app.config.settings import settings

log = logging.getLogger(__name__)

SLACK_POST = "https://slack.com/api/chat.postMessage"


def _blocks(state: RCAState):
    actions  = "\n".join(f"• {a}" for a in state.get("suggested_actions", []))
    conf_pct = int(state.get("confidence", 0.0) * 100)
    return [
        {"type": "header", "text": {"type": "plain_text",
            "text": f"🚨 RCA • {state.get('service_name', 'unknown')}"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Incident:*\n{state.get('incident_id')}"},
            {"type": "mrkdwn", "text": f"*Urgency:*\n{state.get('incident_urgency')}"},
            {"type": "mrkdwn", "text": f"*Title:*\n{state.get('incident_title')}"},
            {"type": "mrkdwn", "text": f"*Confidence:*\n{conf_pct}%"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn",
            "text": f"*Probable root cause*\n{state.get('probable_root_cause', 'n/a')}"}},
        {"type": "section", "text": {"type": "mrkdwn",
            "text": f"*Summary*\n{state.get('rca_summary', 'n/a')}"}},
        {"type": "section", "text": {"type": "mrkdwn",
            "text": f"*Suggested actions*\n{actions or '—'}"}},
        {"type": "context", "elements": [{"type": "mrkdwn",
            "text": f"Sumo source `{state.get('sumo_source')}` • "
                    f"{state.get('sumo_result_count', 0)} log rows analyzed"}]},
    ]


def _is_dry_run() -> bool:
    return settings.slack_dry_run or not settings.slack_bot_token


def slack_notifier(state: RCAState) -> RCAState:
    log.info("▶ node=slack_notifier")
    channel = state.get("slack_channel") or settings.slack_default_channel
    blocks  = _blocks(state)

    if _is_dry_run():
        log.info("  SLACK_DRY_RUN=true — not posting. Would send to %s:", channel)
        log.info("  probable_cause=%s", state.get("probable_root_cause"))
        log.info("  summary=%s", state.get("rca_summary"))
        return {
            **state, "slack_channel": channel, "slack_message_ts": None,
            "slack_delivered": True,  # treat as delivered in dry-run
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    try:
        r = requests.post(
            SLACK_POST,
            headers={"Authorization": f"Bearer {settings.slack_bot_token}",
                     "Content-Type": "application/json; charset=utf-8"},
            json={"channel": channel, "blocks": blocks,
                  "text": f"RCA for {state.get('incident_id')}"},
            timeout=10,
        )
        data = r.json()
        ok, ts = bool(data.get("ok")), data.get("ts")
        if not ok:
            log.error("  slack post failed: %s", data)
        else:
            log.info("  slack posted ts=%s channel=%s", ts, channel)
    except Exception as e:
        log.exception("  slack post error: %s", e)
        ok, ts = False, None

    return {
        **state, "slack_channel": channel, "slack_message_ts": ts,
        "slack_delivered": ok,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
