from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

VALID_STATUSES = {"open", "in_progress", "done"}
VALID_PRIORITIES = {"low", "normal", "high"}
VALID_SOURCE_TYPES = {"manual", "planning_center_people_person", "planning_center_services_person"}


@dataclass(frozen=True)
class Action:
    id: str
    title: str
    source_type: str
    external_id: str
    owner: str
    due_date: str
    priority: str
    status: str
    created_at: str
    updated_at: str


class ActionStore:
    def __init__(self, path: str | Path):
        db_path = Path(path)
        parent = db_path.parent
        if db_path.is_symlink() or parent.is_symlink():
            raise RuntimeError("SQLite path may not be a symlink")
        parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        if parent.stat().st_uid != os.getuid():
            raise RuntimeError("SQLite directory must be owned by the current user")
        parent.chmod(0o700)
        if db_path.exists():
            if not db_path.is_file() or db_path.stat().st_uid != os.getuid():
                raise RuntimeError("SQLite database must be a regular owner-controlled file")
            db_path.chmod(0o600)
        self.path = str(db_path)
        self._initialize()
        self._secure_files()

    def _secure_files(self):
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(self.path + suffix)
            if candidate.exists():
                candidate.chmod(0o600)

    def _connect(self):
        connection = sqlite3.connect(self.path)
        Path(self.path).chmod(0o600)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _schema() -> str:
        return """
            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                external_id TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL,
                due_date TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
                status TEXT NOT NULL CHECK(status IN ('open','in_progress','done')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                FOREIGN KEY(action_id) REFERENCES actions(id)
            );
        """

    def _initialize(self):
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            columns = {row[1] for row in db.execute("PRAGMA table_info(actions)")}
            if "person_label" in columns:
                db.executescript("""
                    ALTER TABLE actions RENAME TO actions_with_person_label;
                    ALTER TABLE audit_events RENAME TO audit_events_old;
                """)
                db.executescript(self._schema())
                db.executescript("""
                    INSERT INTO actions(id,title,source_type,external_id,owner,due_date,priority,status,created_at,updated_at)
                    SELECT id,title,source_type,external_id,owner,due_date,priority,status,created_at,updated_at
                    FROM actions_with_person_label;
                    INSERT INTO audit_events(id,action_id,event_type,occurred_at)
                    SELECT id,action_id,event_type,occurred_at FROM audit_events_old;
                    DROP TABLE audit_events_old;
                    DROP TABLE actions_with_person_label;
                """)
            else:
                db.executescript(self._schema())

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _bounded(value: str, field: str, maximum: int) -> str:
        clean = value.strip()
        if len(clean) > maximum:
            raise ValueError(f"{field} is too long")
        return clean

    def create_action(self, title, source_type, external_id, owner, due_date, priority) -> Action:
        title = self._bounded(title, "title", 200)
        owner = self._bounded(owner, "owner", 100)
        source_type = self._bounded(source_type, "source_type", 64)
        external_id = self._bounded(external_id, "external_id", 128)
        due_date = self._bounded(due_date, "due_date", 10)
        if not title or not owner:
            raise ValueError("title and owner are required")
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError("invalid source type")
        if priority not in VALID_PRIORITIES:
            raise ValueError("invalid priority")
        now, action_id = self._now(), str(uuid4())
        with self._connect() as db:
            db.execute(
                "INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?,?)",
                (action_id, title, source_type, external_id, owner, due_date, priority, "open", now, now),
            )
            db.execute(
                "INSERT INTO audit_events(action_id,event_type,occurred_at) VALUES (?,?,?)",
                (action_id, "action.created", now),
            )
        self._secure_files()
        return self.get(action_id)

    def list_actions(self, *, include_done=False) -> list[Action]:
        sql = (
            "SELECT * FROM actions"
            + ("" if include_done else " WHERE status != 'done'")
            + " ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, due_date = '', due_date, created_at"
        )
        with self._connect() as db:
            return [Action(**dict(row)) for row in db.execute(sql)]

    def get(self, action_id: str) -> Action:
        with self._connect() as db:
            row = db.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
        if not row:
            raise KeyError(action_id)
        return Action(**dict(row))

    def set_status(self, action_id: str, status: str) -> Action:
        if status not in VALID_STATUSES:
            raise ValueError("invalid status")
        now = self._now()
        with self._connect() as db:
            changed = db.execute(
                "UPDATE actions SET status=?, updated_at=? WHERE id=?", (status, now, action_id)
            ).rowcount
            if not changed:
                raise KeyError(action_id)
            db.execute(
                "INSERT INTO audit_events(action_id,event_type,occurred_at) VALUES (?,?,?)",
                (action_id, "action.status_changed", now),
            )
        self._secure_files()
        return self.get(action_id)

    def audit_events(self, action_id: str):
        with self._connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT event_type, occurred_at FROM audit_events WHERE action_id=? ORDER BY id", (action_id,)
                )
            ]
