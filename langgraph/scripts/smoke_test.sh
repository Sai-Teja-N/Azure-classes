#!/usr/bin/env bash
# Fires a fake PagerDuty webhook at the running service.
set -euo pipefail
HOST="${HOST:-http://localhost:8080}"

curl -sS -X POST "$HOST/webhooks/pagerduty" \
  -H 'Content-Type: application/json' \
  -d '{
    "event": {
      "data": {
        "id": "P-SMOKE-001",
        "title": "Checkout API 5xx spike",
        "urgency": "high",
        "created_at": "2026-04-12T14:02:10Z",
        "service": {"summary": "checkout-api"}
      }
    }
  }' | (jq . 2>/dev/null || cat)
