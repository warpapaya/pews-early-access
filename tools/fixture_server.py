"""Sanitized fixture runtime for visual and accessibility acceptance only."""
from __future__ import annotations

import tempfile
from pathlib import Path

from app.main import create_app


class SanitizedFixturePCO:
    def dashboard(self):
        return {
            "connection": {"state": "fresh", "observed_at": "fixture-observation"},
            "plans": [
                {
                    "external_id": "fixture-plan-1",
                    "title": "Sunday Gathering",
                    "dates": "Sun · 10:00 AM",
                    "sort_date": "fixture",
                    "needed_positions_count": 2,
                    "planning_center_url": "https://services.planningcenteronline.com/plans/fixture-plan-1",
                    "source": "planning_center",
                    "observed_at": "fixture-observation",
                },
                {
                    "external_id": "fixture-plan-2",
                    "title": "Midweek Gathering",
                    "dates": "Wed · 6:30 PM",
                    "sort_date": "fixture",
                    "needed_positions_count": 1,
                    "planning_center_url": "https://services.planningcenteronline.com/plans/fixture-plan-2",
                    "source": "planning_center",
                    "observed_at": "fixture-observation",
                },
            ],
            "team_status": {"confirmed": 12, "unconfirmed": 3, "declined": 1, "unknown": 0},
        }

    def search_people(self, query):
        return [{"external_id": "fixture-person-1", "label": "Sample P."}] if query.strip() else []


fixture_root = Path(tempfile.gettempdir()) / "pews-ops-sanitized-fixture"
app = create_app(pco=SanitizedFixturePCO(), db_path=fixture_root / "fixture.db")
