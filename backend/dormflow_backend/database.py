from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

from dormflow.models import DutyStatus, IssueStatus, UserRole
from dormflow.seed import default_announcements, default_duties, default_issues, default_polls


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.session() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    building TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    room TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS duties (
                    duty_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    date_label TEXT NOT NULL,
                    room_scope TEXT NOT NULL,
                    checklist_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS issues (
                    issue_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    room_scope TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS announcements (
                    announcement_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    author TEXT NOT NULL,
                    published_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS polls (
                    poll_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    voters_json TEXT NOT NULL
                );
                """
            )
            self._seed_content(db)

    def _seed_content(self, db: sqlite3.Connection) -> None:
        duties_count = db.execute("SELECT COUNT(*) FROM duties").fetchone()[0]
        if duties_count:
            return
        db.executemany(
            """
            INSERT INTO duties (
                duty_id, title, date_label, room_scope, checklist_json, status, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    duty.duty_id,
                    duty.title,
                    duty.date_label,
                    duty.room_scope,
                    json.dumps(duty.checklist, ensure_ascii=False),
                    duty.status.value,
                    duty.completed_at,
                )
                for duty in default_duties()
            ],
        )
        db.executemany(
            """
            INSERT INTO issues (
                issue_id, title, description, category, room_scope, created_by,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    issue.issue_id,
                    issue.title,
                    issue.description,
                    issue.category,
                    issue.room_scope,
                    issue.created_by,
                    issue.status.value,
                    issue.created_at,
                    issue.updated_at,
                )
                for issue in default_issues()
            ],
        )
        db.executemany(
            """
            INSERT INTO announcements (
                announcement_id, title, body, author, published_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    item.announcement_id,
                    item.title,
                    item.body,
                    item.author,
                    item.published_at,
                )
                for item in default_announcements()
            ],
        )
        db.executemany(
            """
            INSERT INTO polls (
                poll_id, question, options_json, created_by, created_at, voters_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    poll.poll_id,
                    poll.question,
                    json.dumps([_jsonable(asdict(option)) for option in poll.options], ensure_ascii=False),
                    poll.created_by,
                    poll.created_at,
                    json.dumps(poll.voters, ensure_ascii=False),
                )
                for poll in default_polls()
            ],
        )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def user_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "user_id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "building": row["building"],
        "floor": row["floor"],
        "room": row["room"],
        "role": UserRole(row["role"]).value,
    }


def duty_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "duty_id": row["duty_id"],
        "title": row["title"],
        "date_label": row["date_label"],
        "room_scope": row["room_scope"],
        "checklist": json.loads(row["checklist_json"]),
        "status": DutyStatus(row["status"]).value,
        "completed_at": row["completed_at"],
    }


def issue_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "issue_id": row["issue_id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "room_scope": row["room_scope"],
        "created_by": row["created_by"],
        "status": IssueStatus(row["status"]).value,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def announcement_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "announcement_id": row["announcement_id"],
        "title": row["title"],
        "body": row["body"],
        "author": row["author"],
        "published_at": row["published_at"],
    }


def poll_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "poll_id": row["poll_id"],
        "question": row["question"],
        "options": json.loads(row["options_json"]),
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "voters": json.loads(row["voters_json"]),
    }
