from __future__ import annotations

from starlette.testclient import TestClient

from app.main import create_app


class FakePCO:
    def dashboard(self):
        return {
            "connection": {"state": "fresh", "observed_at": "2026-07-24T12:00:00Z"},
            "plans": [{
                "external_id": "42", "title": "Sunday Morning", "dates": "Aug 2",
                "sort_date": "2026-08-02T10:00:00Z", "needed_positions_count": 3,
                "planning_center_url": "https://services.planningcenteronline.com/plans/42",
                "source": "planning_center", "observed_at": "2026-07-24T12:00:00Z",
            }],
            "team_status": {"declined": 2, "unconfirmed": 4, "confirmed": 11, "unknown": 0},
        }

    def search_people(self, query):
        return [{"external_id": "p1", "label": "Jordan R."}]


def client_for(tmp_path):
    return TestClient(create_app(pco=FakePCO(), db_path=tmp_path / "private" / "test.db"))


def test_dashboard_renders_attention_not_vanity_metrics(tmp_path):
    response = client_for(tmp_path).get("/")
    assert response.status_code == 200
    assert "What needs attention" in response.text
    assert "3 unfilled assignment slots" in response.text
    assert "Planning Center" in response.text
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_local_action_creation_requires_session_and_never_persists_person_name(tmp_path):
    client = client_for(tmp_path)
    data = {
        "title": "Follow up", "source_type": "planning_center_people_person", "external_id": "p1",
        "owner": "Care team", "due_date": "2026-07-27", "priority": "high",
    }
    assert client.post("/actions", data=data, follow_redirects=False).status_code == 403
    client.get("/")
    response = client.post("/actions", data=data, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/")
    assert "Follow up" in page.text
    assert "Jordan R." not in page.text


def test_untrusted_host_and_cross_origin_posts_are_rejected(tmp_path):
    client = client_for(tmp_path)
    assert client.get("/health", headers={"host": "attacker.example"}).status_code == 400
    client.get("/")
    response = client.post("/actions", headers={"origin": "https://attacker.example"}, data={
        "title": "Injected", "owner": "Nobody", "priority": "normal",
    })
    assert response.status_code == 403


def test_people_search_uses_request_body_and_session_not_pii_bearing_url(tmp_path):
    client = client_for(tmp_path)
    assert client.post("/api/people/search", data={"q": "Jordan"}).status_code == 403
    client.get("/")
    assert client.get("/api/people", params={"q": "Jordan"}).status_code == 404
    response = client.post("/api/people/search", data={"q": "Jordan"})
    assert response.status_code == 200
    assert response.json()["data"][0]["external_id"] == "p1"


def test_unavailable_source_metrics_are_not_rendered_as_observed_zeroes(tmp_path):
    class UnavailablePCO:
        def dashboard(self):
            return {
                "connection": {
                    "state": "unavailable",
                    "observed_at": "2026-07-24T12:00:00Z",
                    "message": "Planning Center is unavailable.",
                },
                "plans": [],
                "team_status": {"confirmed": None, "unconfirmed": None, "declined": None, "unknown": None},
            }

        def search_people(self, query):
            return []

    client = TestClient(create_app(pco=UnavailablePCO(), db_path=tmp_path / "private" / "unavailable.db"))
    body = client.get("/").text
    assert body.count("Source unavailable") == 3
    assert "0 unfilled assignment slots" not in body
