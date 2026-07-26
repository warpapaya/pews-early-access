from __future__ import annotations

import os

import httpx
import pytest

from app.pco import PCOClient


class StubTransport(httpx.BaseTransport):
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def handle_request(self, request):
        self.requests.append(request)
        payload = self.responses.pop(0)
        return httpx.Response(200, json=payload, request=request)


def test_client_exposes_get_only_and_pins_version():
    transport = StubTransport([{"data": []}])
    client = PCOClient("id", "secret", transport=transport)
    assert not hasattr(client, "request")
    client.get("/services/v2/service_types")
    request = transport.requests[0]
    assert request.method == "GET"
    assert request.headers["x-pco-api-version"] == "2018-11-01"


def test_client_rejects_foreign_or_malformed_urls_before_network():
    client = PCOClient("id", "secret", transport=StubTransport([]))
    for url in [
        "https://evil.example/services/v2/plans",
        "http://api.planningcenteronline.com/services/v2/plans",
        "//evil.example/services/v2/plans",
        "/other/v2/things",
        "/services/v2/plans#fragment",
    ]:
        with pytest.raises(ValueError):
            client.get(url)


def test_client_follows_valid_json_api_next_link_and_deduplicates():
    transport = StubTransport([
        {"data": [{"type": "Plan", "id": "1", "attributes": {"title": "First"}}], "links": {"next": "https://api.planningcenteronline.com/services/v2/plans?offset=1"}},
        {"data": [
            {"type": "Plan", "id": "1", "attributes": {"title": "First"}},
            {"type": "Plan", "id": "2", "attributes": {"title": "Second"}},
        ], "links": {"next": None}},
    ])
    client = PCOClient("id", "secret", transport=transport)
    records = client.get_all("/services/v2/plans")
    assert [record["id"] for record in records] == ["1", "2"]
    assert all(request.method == "GET" for request in transport.requests)
    assert "authorization" not in str(records).lower()


def test_environment_scope_rejects_developer_keys_and_consumes_pat(monkeypatch):
    monkeypatch.setenv("PCO_PAT_CLIENT_ID", "id")
    monkeypatch.setenv("PCO_PAT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("PCO_DEVELOPER_CLIENT_ID", "forbidden")
    with pytest.raises(RuntimeError, match="developer credentials"):
        PCOClient.from_environment()
    monkeypatch.delenv("PCO_DEVELOPER_CLIENT_ID")
    client = PCOClient.from_environment()
    assert client
    assert "PCO_PAT_CLIENT_ID" not in os.environ
    assert "PCO_PAT_CLIENT_SECRET" not in os.environ


def test_dashboard_mapping_uses_fixed_deep_link_not_upstream_url():
    client = PCOClient("id", "secret", transport=StubTransport([]))
    plan = client.map_plan({
        "type": "Plan",
        "id": "42",
        "attributes": {
            "title": "Sunday Morning",
            "dates": "Aug 2",
            "sort_date": "2026-08-02T10:00:00Z",
            "needed_positions_count": 3,
            "planning_center_url": "javascript:alert(1)",
        },
    }, observed_at="2026-07-24T12:00:00Z")
    assert plan.external_id == "42"
    assert plan.source == "planning_center"
    assert plan.needed_positions_count == 3
    assert plan.observed_at == "2026-07-24T12:00:00Z"
    assert plan.planning_center_url == "https://services.planningcenteronline.com/plans/42"


def test_weekly_selection_excludes_past_and_far_future_plans():
    records = [
        ("type", {"id": "past", "attributes": {"sort_date": "2026-07-01T10:00:00Z"}}),
        ("type", {"id": "near", "attributes": {"sort_date": "2026-07-27T10:00:00Z"}}),
        ("type", {"id": "far", "attributes": {"sort_date": "2026-09-01T10:00:00Z"}}),
    ]
    selected = PCOClient.select_upcoming(records, observed_at="2026-07-24T12:00:00Z", horizon_days=14)
    assert [record[1]["id"] for record in selected] == ["near"]


def test_dependency_failure_is_explicitly_unavailable_or_stale():
    empty_client = PCOClient("id", "secret", transport=StubTransport([]))
    unavailable = empty_client.dashboard(cache_seconds=0)
    assert unavailable["connection"]["state"] == "unavailable"
    assert unavailable["plans"] == []
    assert all(value is None for value in unavailable["team_status"].values())

    stale_client = PCOClient("id", "secret", transport=StubTransport([]))
    stale_client._cache = {
        "connection": {"state": "fresh", "observed_at": "2026-07-24T12:00:00Z"},
        "plans": [{"external_id": "opaque"}],
        "team_status": {"confirmed": 1, "unconfirmed": 0, "declined": 0, "unknown": 0},
    }
    stale = stale_client.dashboard(cache_seconds=0)
    assert stale["connection"]["state"] == "stale"
    assert stale["connection"]["observed_at"] == "2026-07-24T12:00:00Z"
    assert stale["plans"] == [{"external_id": "opaque"}]


def test_missing_source_fields_remain_unknown_not_zero():
    client = PCOClient("id", "secret", transport=StubTransport([]))
    plan = client.map_plan(
        {"id": "opaque", "attributes": {"title": "Observed title"}},
        observed_at="2026-07-24T12:00:00Z",
    )
    assert plan.needed_positions_count is None
