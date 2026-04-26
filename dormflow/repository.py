from __future__ import annotations

import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any

from dormflow.models import (
    Announcement,
    Duty,
    DutyStatus,
    Issue,
    IssueStatus,
    Poll,
    PollOption,
    UserProfile,
    UserRole,
)
from dormflow.seed import (
    default_announcements,
    default_duties,
    default_issues,
    default_polls,
    default_profile,
)


class JsonRepository:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def ensure_seeded(self) -> None:
        if self.file_path.exists():
            return
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "profile": self._to_jsonable(asdict(default_profile())),
            "duties": [self._to_jsonable(asdict(item)) for item in default_duties()],
            "issues": [self._to_jsonable(asdict(item)) for item in default_issues()],
            "announcements": [self._to_jsonable(asdict(item)) for item in default_announcements()],
            "polls": [self._poll_to_dict(item) for item in default_polls()],
        }
        self.file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> dict[str, Any]:
        self.ensure_seeded()
        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        return {
            "profile": self._profile_from_dict(raw.get("profile", {})),
            "duties": [self._duty_from_dict(item) for item in raw.get("duties", [])],
            "issues": [self._issue_from_dict(item) for item in raw.get("issues", [])],
            "announcements": [
                self._announcement_from_dict(item) for item in raw.get("announcements", [])
            ],
            "polls": [self._poll_from_dict(item) for item in raw.get("polls", [])],
        }

    def save(self, payload: dict[str, Any]) -> None:
        prepared = {
            "profile": self._to_jsonable(asdict(payload["profile"])),
            "duties": [self._to_jsonable(asdict(item)) for item in payload["duties"]],
            "issues": [self._to_jsonable(asdict(item)) for item in payload["issues"]],
            "announcements": [self._to_jsonable(asdict(item)) for item in payload["announcements"]],
            "polls": [self._poll_to_dict(item) for item in payload["polls"]],
        }
        self.file_path.write_text(
            json.dumps(prepared, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _profile_from_dict(data: dict[str, Any]) -> UserProfile:
        role_raw = data.get("role", UserRole.RESIDENT)
        role = UserRole(role_raw)
        return UserProfile(
            name=data.get("name", "Пользователь"),
            building=data.get("building", "Корпус"),
            floor=data.get("floor", "?"),
            room=data.get("room", "?"),
            role=role,
            email=data.get("email", ""),
            user_id=data.get("user_id"),
        )

    @staticmethod
    def _duty_from_dict(data: dict[str, Any]) -> Duty:
        payload = dict(data)
        payload["status"] = DutyStatus(payload.get("status", DutyStatus.PENDING))
        return Duty(**payload)

    @staticmethod
    def _issue_from_dict(data: dict[str, Any]) -> Issue:
        payload = dict(data)
        payload["status"] = IssueStatus(payload.get("status", IssueStatus.NEW))
        return Issue(**payload)

    @staticmethod
    def _announcement_from_dict(data: dict[str, Any]) -> Announcement:
        return Announcement(**data)

    @staticmethod
    def _poll_from_dict(data: dict[str, Any]) -> Poll:
        options = [PollOption(**option_data) for option_data in data.get("options", [])]
        return Poll(
            poll_id=data["poll_id"],
            question=data["question"],
            options=options,
            created_by=data["created_by"],
            created_at=data.get("created_at", ""),
            voters=data.get("voters", []),
        )

    @staticmethod
    def _poll_to_dict(item: Poll) -> dict[str, Any]:
        result = asdict(item)
        result["options"] = [asdict(option) for option in item.options]
        return JsonRepository._to_jsonable(result)

    @staticmethod
    def _to_jsonable(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: JsonRepository._to_jsonable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [JsonRepository._to_jsonable(item) for item in value]
        return value
