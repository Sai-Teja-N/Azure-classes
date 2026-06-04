"""Runtime settings loaded from env vars."""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    # --- LLM (provider-agnostic; actual client built in app/llm/factory.py) ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "bedrock")
    llm_model:    str = os.getenv("LLM_MODEL", "")

    # --- SumoLogic ---
    sumo_access_id:  str = os.getenv("SUMO_ACCESS_ID", "")
    sumo_access_key: str = os.getenv("SUMO_ACCESS_KEY", "")
    sumo_endpoint:   str = os.getenv("SUMO_ENDPOINT", "https://api.au.sumologic.com/api/v1")
    sumologic_enabled: bool = os.getenv("SUMOLOGIC_ENABLED", "true").lower() == "true"
    sumo_local_file_path: str = os.getenv("SUMO_LOCAL_FILE_PATH", "")


    # --- Slack ---
    slack_bot_token:        str = os.getenv("SLACK_BOT_TOKEN", "")
    slack_default_channel:  str = os.getenv("SLACK_CHANNEL", "#incidents")
    slack_dry_run:          bool = os.getenv("SLACK_DRY_RUN", "false").lower() == "true"

    # --- PagerDuty ---
    pd_webhook_secret: str = os.getenv("PD_WEBHOOK_SECRET", "")

    # --- Redis (cache + checkpointer) ---
    redis_url:         str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL", "900"))
    # Falls back to in-memory cache/checkpointer when Redis is unavailable.
    use_redis:         bool = os.getenv("USE_REDIS", "true").lower() == "true"

    # --- App ---
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()
