from __future__ import annotations

import sqlite3

import pytest

from app.store import ActionStore


def test_action_lifecycle_is_local_minimal_and_audited(tmp_path):
    store = ActionStore(tmp_path / "private" / "pews.db")
    action = store.create_action(
        title="Call first-time guest",
        source_type="planning_center_people_person",
        external_id="person-123",
        owner="Pastoral care",
        due_date="2026-07-27",
        priority="high",
    )
    assert action.status == "open"
    updated = store.set_status(action.id, "done")
    assert updated.status == "done"
    events = store.audit_events(action.id)
    assert [event["event_type"] for event in events] == ["action.created", "action.status_changed"]
    with sqlite3.connect(store.path) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(actions)")}
    assert "person_label" not in columns
    assert (tmp_path / "private").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "private" / "pews.db").stat().st_mode & 0o777 == 0o600


def test_store_rejects_invalid_status_priority_and_oversized_text(tmp_path):
    store = ActionStore(tmp_path / "pews.db")
    with pytest.raises(ValueError, match="priority"):
        store.create_action("Bad", "manual", "", "Owner", "", "urgentest")
    with pytest.raises(ValueError, match="too long"):
        store.create_action("x" * 201, "manual", "", "Owner", "", "normal")


def test_store_rejects_symlinked_database_path(tmp_path):
    target = tmp_path / "target.db"
    target.touch()
    link = tmp_path / "linked.db"
    link.symlink_to(target)
    with pytest.raises(RuntimeError, match="symlink"):
        ActionStore(link)
