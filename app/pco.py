from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx


@dataclass(frozen=True)
class Plan:
    external_id: str
    title: str
    dates: str
    sort_date: str
    needed_positions_count: int | None
    planning_center_url: str
    source: str
    observed_at: str


class PCOClient:
    BASE_URL = "https://api.planningcenteronline.com"
    _ALLOWED_PATHS = ("/services/v2/", "/people/v2/")
    _OPAQUE_ID = re.compile(r"^[A-Za-z0-9_-]+$")

    def __init__(self, client_id: str, client_secret: str, *, transport=None, timeout: float = 20.0):
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            auth=(client_id, client_secret),
            headers={"Accept": "application/json", "User-Agent": "Pews-Ops-Local-Beta/0.1"},
            transport=transport,
            timeout=timeout,
            follow_redirects=False,
        )
        self._cache: dict[str, Any] = {}
        self._cache_at = 0.0
        self._lock = threading.Lock()

    @classmethod
    def from_environment(cls) -> PCOClient:
        if os.environ.get("PCO_DEVELOPER_CLIENT_ID") or os.environ.get("PCO_DEVELOPER_CLIENT_SECRET"):
            raise RuntimeError("OAuth developer credentials are forbidden in the PAT data-plane process")
        client_id = os.environ.pop("PCO_PAT_CLIENT_ID")
        client_secret = os.environ.pop("PCO_PAT_CLIENT_SECRET")
        return cls(client_id, client_secret)

    @classmethod
    def _validated_path(cls, value: str) -> tuple[str, str]:
        parsed = urlsplit(value)
        if parsed.fragment or parsed.username or parsed.password:
            raise ValueError("Unsafe Planning Center URL")
        if parsed.scheme or parsed.netloc:
            if parsed.scheme != "https" or parsed.hostname != "api.planningcenteronline.com" or parsed.port not in {None, 443}:
                raise ValueError("Planning Center URL authority is not allowed")
        elif not value.startswith("/") or value.startswith("//"):
            raise ValueError("Planning Center path must be absolute and local to the API origin")
        if not parsed.path.startswith(cls._ALLOWED_PATHS):
            raise ValueError("Planning Center path family is not allowed")
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        version = "2018-11-01" if parsed.path.startswith("/services/v2/") else "2026-06-04"
        return path, version

    def get(self, path: str) -> dict[str, Any]:
        safe_path, version = self._validated_path(path)
        response = self._client.get(safe_path, headers={"X-PCO-API-Version": version})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or "data" not in payload:
            raise ValueError("Planning Center returned an invalid JSON:API document")
        return payload

    def get_all(self, path: str, *, max_pages: int = 20) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        next_path: str | None = path
        pages = 0
        while next_path and pages < max_pages:
            payload = self.get(next_path)
            data = payload.get("data", [])
            if not isinstance(data, list):
                raise TypeError("Expected a JSON:API collection")
            for record in data:
                if not isinstance(record, dict) or "id" not in record:
                    raise TypeError("Expected a JSON:API resource")
                key = (str(record.get("type") or ""), str(record["id"]))
                if key not in seen:
                    records.append(record)
                    seen.add(key)
            candidate = (payload.get("links") or {}).get("next")
            if candidate is not None and not isinstance(candidate, str):
                raise TypeError("Invalid JSON:API next link")
            next_path = candidate
            pages += 1
        return records

    def map_plan(self, record: dict[str, Any], *, observed_at: str) -> Plan:
        attrs = record.get("attributes") or {}
        external_id = str(record["id"])
        deep_link = ""
        if self._OPAQUE_ID.fullmatch(external_id):
            deep_link = f"https://services.planningcenteronline.com/plans/{external_id}"
        return Plan(
            external_id=external_id,
            title=str(attrs.get("title") or attrs.get("series_title") or "Untitled service"),
            dates=str(attrs.get("dates") or "Date unavailable"),
            sort_date=str(attrs.get("sort_date") or ""),
            needed_positions_count=(
                max(0, int(attrs["needed_positions_count"]))
                if attrs.get("needed_positions_count") is not None
                else None
            ),
            planning_center_url=deep_link,
            source="planning_center",
            observed_at=observed_at,
        )

    @staticmethod
    def select_upcoming(
        records: list[tuple[str, dict[str, Any]]], *, observed_at: str, horizon_days: int = 7
    ) -> list[tuple[str, dict[str, Any]]]:
        start = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        end = start + timedelta(days=horizon_days)
        selected = []
        for service_type_id, record in records:
            raw = str((record.get("attributes") or {}).get("sort_date") or "")
            try:
                sort_date = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if start <= sort_date <= end:
                selected.append((service_type_id, record))
        selected.sort(key=lambda pair: (pair[1].get("attributes") or {}).get("sort_date") or "")
        return selected

    def dashboard(self, *, cache_seconds: int = 300) -> dict[str, Any]:
        with self._lock:
            if self._cache and time.monotonic() - self._cache_at < cache_seconds:
                return self._cache
            observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            try:
                service_types = self.get_all(
                    "/services/v2/service_types?per_page=100&fields[ServiceType]=name,archived_at,deleted_at",
                    max_pages=2,
                )
                plans_with_type: list[tuple[str, dict[str, Any]]] = []
                for service_type in service_types:
                    attrs = service_type.get("attributes") or {}
                    if attrs.get("archived_at") or attrs.get("deleted_at"):
                        continue
                    sid = str(service_type["id"])
                    plans = self.get_all(
                        f"/services/v2/service_types/{sid}/plans?filter=future&order=sort_date&per_page=5"
                        "&fields[Plan]=title,series_title,dates,sort_date,needed_positions_count",
                        max_pages=1,
                    )
                    plans_with_type.extend((sid, plan) for plan in plans)
                plans_with_type = self.select_upcoming(plans_with_type, observed_at=observed_at)[:8]
                team_status = {"confirmed": 0, "unconfirmed": 0, "declined": 0, "unknown": 0}
                for sid, plan in plans_with_type[:4]:
                    pid = str(plan["id"])
                    members = self.get_all(
                        f"/services/v2/service_types/{sid}/plans/{pid}/team_members?per_page=100"
                        "&fields[PlanPerson]=status,status_updated_at,team_position_name,updated_at",
                        max_pages=2,
                    )
                    for member in members:
                        status = str((member.get("attributes") or {}).get("status") or "").lower()
                        if status in {"c", "confirmed"}:
                            team_status["confirmed"] += 1
                        elif status in {"u", "unconfirmed"}:
                            team_status["unconfirmed"] += 1
                        elif status in {"d", "declined"}:
                            team_status["declined"] += 1
                        else:
                            team_status["unknown"] += 1
                result = {
                    "connection": {"state": "fresh", "observed_at": observed_at},
                    "plans": [asdict(self.map_plan(plan, observed_at=observed_at)) for _, plan in plans_with_type],
                    "team_status": team_status,
                }
                self._cache = result
                self._cache_at = time.monotonic()
                return result
            except Exception:  # noqa: BLE001 - dependency failure must fail closed to stale/unavailable state
                if self._cache:
                    stale = dict(self._cache)
                    stale["connection"] = {
                        "state": "stale",
                        "observed_at": self._cache["connection"]["observed_at"],
                        "message": "Planning Center could not be refreshed. Showing the last successful read.",
                    }
                    return stale
                return {
                    "connection": {
                        "state": "unavailable",
                        "observed_at": observed_at,
                        "message": "Planning Center is unavailable. No source data is being inferred.",
                    },
                    "plans": [],
                    "team_status": {
                        "confirmed": None,
                        "unconfirmed": None,
                        "declined": None,
                        "unknown": None,
                    },
                }

    def search_people(self, query: str) -> list[dict[str, str]]:
        query = query.strip()
        if len(query) < 2:
            return []
        params = urlencode({
            "where[search_name]": query,
            "per_page": "10",
            "fields[Person]": "first_name,last_name,status,inactivated_at,updated_at",
        })
        payload = self.get(f"/people/v2/people?{params}")
        people = []
        for record in payload.get("data", []):
            attrs = record.get("attributes") or {}
            first = str(attrs.get("first_name") or "").strip()
            last = str(attrs.get("last_name") or "").strip()
            label = f"{first} {last[:1] + '.' if last else ''}".strip()
            people.append({"external_id": str(record["id"]), "label": label or "Unnamed person"})
        return people
