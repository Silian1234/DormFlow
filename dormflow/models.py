from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    RESIDENT = "resident"
    HEADMAN = "headman"


class DutyStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"


class IssueStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass(slots=True)
class UserProfile:
    name: str
    building: str
    floor: str
    room: str
    role: UserRole = UserRole.RESIDENT
    email: str = ""
    user_id: int | None = None


@dataclass(slots=True)
class Duty:
    duty_id: str
    title: str
    date_label: str
    room_scope: str
    checklist: list[str]
    status: DutyStatus = DutyStatus.PENDING
    completed_at: str | None = None


@dataclass(slots=True)
class Issue:
    issue_id: str
    title: str
    description: str
    category: str
    room_scope: str
    created_by: str
    status: IssueStatus = IssueStatus.NEW
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass(slots=True)
class Announcement:
    announcement_id: str
    title: str
    body: str
    author: str
    published_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass(slots=True)
class PollOption:
    text: str
    votes: int = 0


@dataclass(slots=True)
class Poll:
    poll_id: str
    question: str
    options: list[PollOption]
    created_by: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    voters: list[str] = field(default_factory=list)
