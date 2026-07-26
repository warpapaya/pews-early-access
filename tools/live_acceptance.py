from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pco import PCOClient

client = PCOClient.from_environment()
dashboard = client.dashboard(cache_seconds=0)
assert dashboard["connection"]["state"] == "fresh", dashboard["connection"]
observed = datetime.fromisoformat(dashboard["connection"]["observed_at"].replace("Z", "+00:00"))
plan_dates = [datetime.fromisoformat(plan["sort_date"].replace("Z", "+00:00")) for plan in dashboard["plans"]]
assert plan_dates, "No plans in the 7-day operational horizon"
assert all(0 <= (date - observed).total_seconds() <= 7 * 86400 for date in plan_dates)
assert all(plan["source"] == "planning_center" and plan["observed_at"] for plan in dashboard["plans"])
print(json.dumps({
    "connection": "fresh",
    "read_only": True,
    "plans_in_7_day_horizon": len(plan_dates),
    "max_days_ahead": round(max((date - observed).total_seconds() for date in plan_dates) / 86400, 2),
    "open_positions_total": sum(plan["needed_positions_count"] for plan in dashboard["plans"]),
    "team_status_keys": sorted(dashboard["team_status"]),
}))
