import os
import json
from app.state import RCAState

# Override config directly since module might be loaded
from app.config.settings import settings
settings.sumologic_enabled = False
settings.sumo_local_file_path = "test_local.json"

from app.nodes.sumo_fetcher import sumo_fetcher

# Create dummy local json file
with open("test_local.json", "w") as f:
    json.dump([{"_raw": "fake log from local file"}], f)

state = {
    "sumo_source": "test",
    "service_name": "test",
    "time_range_minutes": 30,
}
res = sumo_fetcher(state)
print("SUMO_RESULTS:", res.get("sumo_results"))
