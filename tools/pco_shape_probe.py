"""Read-only, value-redacting Planning Center API shape probe."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from app.pco import PCOClient


def inspect_shape(client: PCOClient, path: str):
    clean_path = re.sub(r"/\d+(?=/|$)", "/{id}", path.split("?", 1)[0])
    try:
        body = client.get(path)
        data = body.get("data")
        if isinstance(data, list):
            sample = data[0] if data else {}
            result = {
                "path": clean_path,
                "status": 200,
                "count_page": len(data),
                "meta_keys": sorted((body.get("meta") or {}).keys()),
                "sample_type": sample.get("type"),
                "sample_attribute_keys": sorted((sample.get("attributes") or {}).keys()),
                "sample_relationship_keys": sorted((sample.get("relationships") or {}).keys()),
            }
        else:
            data = data or {}
            result = {
                "path": clean_path,
                "status": 200,
                "type": data.get("type"),
                "attribute_keys": sorted((data.get("attributes") or {}).keys()),
                "relationship_keys": sorted((data.get("relationships") or {}).keys()),
            }
        print(json.dumps(result, sort_keys=True))
        return body
    except (httpx.HTTPError, TypeError, ValueError) as error:
        status = error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
        print(json.dumps({"path": clean_path, "status": status, "error": type(error).__name__}))
        return None


def main() -> None:
    client = PCOClient.from_environment()
    inspect_shape(client, "/people/v2/me?fields[Person]=status")
    service_types = inspect_shape(
        client,
        "/services/v2/service_types?per_page=100&fields[ServiceType]=name,archived_at,deleted_at",
    )
    if not service_types or not service_types.get("data"):
        return
    service_type_id = service_types["data"][0]["id"]
    plans = inspect_shape(
        client,
        f"/services/v2/service_types/{service_type_id}/plans?filter=future&per_page=10"
        "&fields[Plan]=title,series_title,dates,sort_date,needed_positions_count",
    )
    if not plans or not plans.get("data"):
        return
    plan_id = plans["data"][0]["id"]
    inspect_shape(
        client,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/team_members?per_page=100"
        "&fields[PlanPerson]=status,status_updated_at,team_position_name,updated_at",
    )
    inspect_shape(
        client,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/needed_positions?per_page=100"
        "&fields[NeededPosition]=quantity,team_position_name",
    )


if __name__ == "__main__":
    main()
