# RCA LangGraph Service

An automated **Root Cause Analysis** pipeline: a PagerDuty incident comes in → the service pulls relevant logs from SumoLogic → an LLM summarizes the likely root cause → a formatted RCA is posted to Slack. Built as a 4-node [LangGraph](https://langchain-ai.github.io/langgraph/) application, works with **any major LLM provider**, and ships as a Docker container.

---

## Table of contents
1. [Architecture](#architecture)
2. [What each file does](#what-each-file-does)
3. [Tools & libraries used](#tools--libraries-used)
4. [LLM providers supported](#llm-providers-supported)
5. [Quick start (zero-credential dry-run)](#quick-start-zero-credential-dry-run)
6. [Running with real credentials](#running-with-real-credentials)
7. [Testing with Postman](#testing-with-postman)
8. [Logging](#logging)
9. [Environment variables](#environment-variables)
10. [Project layout](#project-layout)

---

## Architecture

```
PagerDuty ──► FastAPI /webhooks/pagerduty
                    │
                    ▼
    ┌───────────────────────────────────┐
    │     LangGraph StateGraph           │
    │     (Redis or in-memory)           │
    └───────────────────────────────────┘
         │           │            │           │
         ▼           ▼            ▼           ▼
  pd_collector → sumo_fetcher → llm_analyzer → slack_notifier
   parse+map      query logs    Bedrock LLM   post RCA
```

Every node reads and writes a single **`RCAState`** TypedDict. Two forms of memory sit behind the graph:

- **Checkpointer** — persists each step keyed by `thread_id = incident_id`. Lets you inspect/resume runs. Uses `RedisSaver` if Redis is reachable, otherwise falls back to LangGraph's `MemorySaver`.
- **Application cache** — dedup, Sumo result cache, LLM output cache (by log fingerprint). Redis when available, in-process dict otherwise.

---

## What each file does

### `app/main.py`
FastAPI app. Initializes logging, exposes `GET /healthz` and `POST /webhooks/pagerduty`. The webhook extracts the incident payload, calls `graph.invoke()` with `thread_id = incident_id`, and returns the final state as JSON.

### `app/graph.py`
Builds the LangGraph `StateGraph`: registers the four nodes, wires them linearly, and attaches a checkpointer. The checkpointer degrades gracefully from Redis → in-memory so the service runs even without Redis.

### `app/state.py`
`RCAState` TypedDict — the single shape that flows through all nodes. Think of it as the conversation's "working memory."

### `app/config/settings.py`
Central `Settings` dataclass reading from env vars. Includes `*_DRY_RUN` switches for Sumo/Slack and `USE_REDIS` to disable the Redis dependency entirely.

### `app/nodes/pd_collector.py` — Node 1
Parses the PagerDuty payload (supports PDv3 and flattened formats), maps `service → sumo_source` via a small dict (swap for a CMDB lookup later), and dedups repeat webhooks via a 10-min Redis key.

### `app/nodes/sumo_fetcher.py` — Node 2
Runs a SumoLogic search job against the mapped source for the last 30 min, polls until done, returns messages. Results are cached for 5 min.

### `app/nodes/llm_analyzer.py` — Node 3
Builds a prompt (system + user), pipes it through `prompt | llm | JsonOutputParser`, and expects strict JSON back (`rca_summary`, `probable_root_cause`, `suggested_actions`, `confidence`). Caches the LLM output keyed by `(incident_id, sha256(logs))` so identical log payloads don't re-bill you.

### `app/llm/factory.py`
**The key piece for provider-agnosticism.** Reads `LLM_PROVIDER` and returns the right LangChain chat model. Supported values: `bedrock` (default), `azure`.

### `app/nodes/slack_notifier.py` — Node 4
Formats the RCA as Slack Block Kit and calls `chat.postMessage`. **In dry-run mode (`SLACK_DRY_RUN=true`) logs what it would send** instead of hitting the API.

### `app/utils/cache.py`
Thin Redis wrapper with an automatic fallback to an in-memory TTL dict. Exports `get`, `set`, `cache_key(ns, *parts)`, `fingerprint_logs(list)`.

### `app/utils/logging_setup.py`
Configures the root logger with a console handler + a `RotatingFileHandler` (5 MB × 5 files) writing to `$LOG_DIR/rca.log`. Called once at startup from `app/main.py`.

### `deploy/Dockerfile`
Slim Python 3.11 image, installs deps, copies `app/`, exposes `8080`, mounts `/srv/logs` as a volume, includes a health check.

### `deploy/docker-compose.yml`
Brings up `rca-app` + `redis`, mounts `./logs` from the host so log files survive container restarts.

### `postman/`
- `RCA_PagerDuty.postman_collection.json` — 6 ready-to-send requests (health check + 5 dummy incidents).
- `RCA_Local.postman_environment.json` — sets `base_url=http://localhost:8080`.

### `scripts/smoke_test.sh`
One-shot `curl` test. Pipes response through `jq` if available.

---

## Tools & libraries used

| Tool | Purpose |
|---|---|
| **FastAPI** | HTTP webhook receiver |
| **Uvicorn** | ASGI server (2 workers in the container) |
| **LangGraph** | Stateful graph runtime (nodes, edges, checkpointer) |
| **LangChain core** | Prompt templates, `JsonOutputParser`, LCEL chaining |
| **langchain-openai** | Optional provider-specific client for Azure |
| **Redis** | Optional cache + checkpointer backend |
| **Docker + docker-compose** | Container packaging & local orchestration |
| **Postman** | Dummy PagerDuty payload testing |
| **Python `logging` + `RotatingFileHandler`** | Dual console/file logs with rotation |
| **`requests`** | SumoLogic search job + Slack posting |

---

## LLM providers supported

Switch by setting `LLM_PROVIDER` in `.env`:

| Provider | `LLM_PROVIDER` | Required env | Suggested `LLM_MODEL` |
|---|---|---|---|
| **AWS Bedrock** | `bedrock` | `AWS_PROFILE` (or `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`) | `amazon.nova-micro-v1:0` |
| Azure OpenAI | `azure` | `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` | deployment name |

The pipeline code doesn't care which one — the factory returns any LangChain chat model and the rest of the chain works unchanged.

---

You can run the pipeline end-to-end — copy `.env.example` (which defaults to `LLM_PROVIDER=bedrock`). Combined with `SLACK_DRY_RUN=true`, `USE_REDIS=false`.

```bash
git clone <your-repo> rca-langgraph && cd rca-langgraph
cp .env.example .env
pip install -r requirements.txt
make run-local        # or: uvicorn app.main:app --reload --port 8080
```

In another terminal:

```bash
make smoke            # or: ./scripts/smoke_test.sh
tail -f logs/rca.log  # watch the file log
```

You'll see all four nodes execute and a JSON response containing the canned RCA summary.

### Or via Docker:
```bash
cp .env.example .env
make build && make up
make logs             # container logs (includes file logs too)
```

---

## Running with real credentials

Edit `.env`:

```dotenv
LLM_PROVIDER=bedrock
LLM_MODEL=amazon.nova-micro-v1:0
AWS_PROFILE=rca-bedrock
AWS_DEFAULT_REGION=us-east-1

SUMO_ACCESS_ID=...
SUMO_ACCESS_KEY=...

SLACK_DRY_RUN=false
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#incidents

USE_REDIS=true
```

Then `make up`. Point PagerDuty's Generic Webhook extension at:
```
https://<your-public-host>/webhooks/pagerduty
```

---

## Testing with Postman

1. Open Postman → **Import** → drop in both files from `postman/`:
   - `RCA_PagerDuty.postman_collection.json`
   - `RCA_Local.postman_environment.json`
2. Select the **RCA Local** environment (top-right).
3. Make sure the service is running (`make run-local` or `make up`).
4. Send any request in the collection:

| Request | Triggers |
|---|---|
| `Health check` | `GET /healthz` → `{"status":"ok"}` |
| `PD webhook — checkout-api 5xx spike` | Node 1 maps to `prod/checkout-api`, returns a full RCA |
| `PD webhook — payments-svc timeout` | Maps to `prod/payments` |
| `PD webhook — auth-gateway degradation` | Low-urgency path |
| `PD webhook — orders-db connection errors` | Database-flavored incident |
| `PD webhook — flattened payload` | Tests the legacy (non-v3) parser branch |

In dry-run mode the response body includes the full RCA the LLM produced. In real mode, check Slack for the posted message.

### Point Postman at a remote host
Change the collection variable `base_url` (or the environment variable) to your host/port.

---

## Logging

Logs go to **both the console and a rotating file**:

- **File**: `$LOG_DIR/$LOG_FILE` → defaults to `./logs/rca.log`
- **Rotation**: 5 MB per file, keeps 5 backups (`rca.log.1` … `rca.log.5`)
- **Level**: `LOG_LEVEL=INFO` by default; set to `DEBUG` for verbose traces
- **Format**: `2026-04-12 14:02:11 INFO  [rca.api] ↩ received PD webhook incident=P-123`

Each node logs a `▶ node=<name>` line at entry so you can trace graph execution. In Docker, `./logs` is bind-mounted from the host, so logs persist across container restarts.

**Quick tail**:
```bash
make tail-log              # tails logs/rca.log
make logs                  # tails container stdout
```

---

## Environment variables

See `.env.example` for the full list. The important ones:

| Var | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `bedrock` | Which LangChain chat model to build |
| `LLM_MODEL` | provider-specific | Override the default model |
| `LLM_TEMPERATURE` | `0.2` | |
| `LLM_MAX_TOKENS` | `1024` | |

| `SLACK_DRY_RUN` | `false` | Log message instead of posting |
| `USE_REDIS` | `true` | Disable for pure in-memory mode |
| `REDIS_URL` | `redis://redis:6379/0` | |
| `CACHE_TTL` | `900` | Default cache TTL in seconds |
| `LOG_LEVEL` | `INFO` | |
| `LOG_DIR` | `./logs` | |
| `LOG_FILE` | `rca.log` | |

---

## Project layout

```
rca-langgraph/
├── app/
│   ├── __init__.py
│   ├── main.py                    FastAPI entrypoint
│   ├── graph.py                   LangGraph assembly
│   ├── state.py                   RCAState TypedDict
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── factory.py             ⭐ provider-agnostic LLM builder
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── pd_collector.py        Node 1
│   │   ├── sumo_fetcher.py        Node 2 (supports SUMO_DRY_RUN)
│   │   ├── llm_analyzer.py        Node 3 (uses factory)
│   │   └── slack_notifier.py      Node 4 (supports SLACK_DRY_RUN)
│   └── utils/
│       ├── __init__.py
│       ├── cache.py               Redis + in-memory fallback
│       └── logging_setup.py       Console + rotating file log
├── postman/
│   ├── RCA_PagerDuty.postman_collection.json
│   └── RCA_Local.postman_environment.json
├── scripts/
│   └── smoke_test.sh
├── deploy/
│   ├── Dockerfile
│   └── docker-compose.yml
├── logs/                          created at runtime
├── requirements.txt
├── .env.example
├── Makefile
└── README.md
```

---

## Extending

- **Add a new LLM provider**: add a `_myprovider(...)` function in `app/llm/factory.py` and register it in `_PROVIDERS`.
- **Add a new RCA step** (e.g. create a Jira ticket): write a `jira_creator` node, add it between `llm_analyzer` and `slack_notifier` in `graph.py`, extend `RCAState` with the new fields.
- **Conditional routing**: replace `add_edge` with `add_conditional_edges` in `graph.py` — e.g. skip the LLM if `sumo_result_count == 0` and post a "no logs found" message instead.
