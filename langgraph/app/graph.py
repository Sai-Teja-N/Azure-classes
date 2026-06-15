"""Assemble the LangGraph StateGraph: 4 nodes + optional Redis checkpointer.

Falls back to an in-memory checkpointer when Redis isn't reachable, so the
pipeline is fully runnable locally without dependencies.
"""
import logging
from langgraph.graph import StateGraph, START, END

from app.state import RCAState
from app.config.settings import settings
from app.nodes.pd_collector   import pd_collector
from app.nodes.sumo_fetcher   import sumo_fetcher
from app.nodes.llm_analyzer   import llm_analyzer
from app.nodes.slack_notifier import slack_notifier

log = logging.getLogger(__name__)


def _checkpointer():
    if not settings.use_redis:
        from langgraph.checkpoint.memory import MemorySaver
        log.info("checkpointer: in-memory (USE_REDIS=false)")
        return MemorySaver()
    try:
        from langgraph.checkpoint.redis import RedisSaver
        cp_manager = RedisSaver.from_conn_string(settings.redis_url)
        cp = cp_manager.__enter__()
        log.info("checkpointer: redis at %s", settings.redis_url)
        return cp
    except Exception as e:
        from langgraph.checkpoint.memory import MemorySaver
        log.warning("checkpointer: redis unavailable (%s) — using in-memory", e)
        return MemorySaver()


def build_graph():
    g = StateGraph(RCAState)
    g.add_node("pd_collector",   pd_collector)
    g.add_node("sumo_fetcher",   sumo_fetcher)
    g.add_node("llm_analyzer",   llm_analyzer)
    g.add_node("slack_notifier", slack_notifier)

    g.add_edge(START,            "pd_collector")
    g.add_edge("pd_collector",   "sumo_fetcher")
    g.add_edge("sumo_fetcher",   "llm_analyzer")
    g.add_edge("llm_analyzer",   "slack_notifier")
    g.add_edge("slack_notifier", END)

    return g.compile(checkpointer=_checkpointer())


graph = build_graph()
