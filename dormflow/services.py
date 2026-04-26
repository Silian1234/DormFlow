from __future__ import annotations

from datetime import datetime
from pathlib import Path

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
from dormflow.repository import JsonRepository


class DormFlowService:
    def __init__(self, storage_path: Path) -> None:
        self.repository = JsonRepository(storage_path)
        self.payload = self.repository.load()

    def save(self) -> None:
        self.repository.save(self.payload)

    def get_profile(self) -> UserProfile:
        return self.payload["profile"]

    def switch_role(self, role: UserRole) -> None:
        profile = self.get_profile()
        profile.role = role
        self.save()

    def list_duties(self) -> list[Duty]:
        return sorted(
            self.payload["duties"],
            key=lambda item: item.date_label,
        )

    def mark_duty_done(self, duty_id: str) -> bool:
        duty = self.find_duty(duty_id)
        if duty is None:
            return False
        duty.status = DutyStatus.DONE
        duty.completed_at = datetime.now().isoformat(timespec="seconds")
        self.save()
        return True

    def create_duty(self, title: str, date_label: str, room_scope: str, checklist: list[str]) -> Duty:
        clean_checklist = [item.strip() for item in checklist if item.strip()]
        duty = Duty(
            duty_id=f"duty-{len(self.payload['duties']) + 1:03d}",
            title=title.strip(),
            date_label=date_label.strip(),
            room_scope=room_scope.strip(),
            checklist=clean_checklist,
            status=DutyStatus.PENDING,
        )
        self.payload["duties"].insert(0, duty)
        self.save()
        return duty

    def find_duty(self, duty_id: str) -> Duty | None:
        for duty in self.payload["duties"]:
            if duty.duty_id == duty_id:
                return duty
        return None

    def list_issues(self) -> list[Issue]:
        return sorted(self.payload["issues"], key=lambda item: item.updated_at, reverse=True)

    def find_issue(self, issue_id: str) -> Issue | None:
        for issue in self.payload["issues"]:
            if issue.issue_id == issue_id:
                return issue
        return None

    def create_issue(self, title: str, description: str, category: str) -> Issue:
        issue = Issue(
            issue_id=self._next_issue_id(),
            title=title.strip(),
            description=description.strip(),
            category=category.strip() or "Другое",
            room_scope=f"Этаж {self.get_profile().floor}",
            created_by=self.get_profile().name,
            status=IssueStatus.NEW,
        )
        self.payload["issues"].insert(0, issue)
        self.save()
        return issue

    def move_issue_status(self, issue_id: str) -> Issue | None:
        issue = self.find_issue(issue_id)
        if issue is None:
            return None
        if issue.status == IssueStatus.NEW:
            issue.status = IssueStatus.IN_PROGRESS
        elif issue.status == IssueStatus.IN_PROGRESS:
            issue.status = IssueStatus.DONE
        issue.updated_at = datetime.now().isoformat(timespec="seconds")
        self.save()
        return issue

    def list_announcements(self) -> list[Announcement]:
        return sorted(self.payload["announcements"], key=lambda item: item.published_at, reverse=True)

    def create_announcement(self, title: str, body: str) -> Announcement:
        item = Announcement(
            announcement_id=self._next_announcement_id(),
            title=title.strip(),
            body=body.strip(),
            author=self.get_profile().name if self.get_profile().role == UserRole.HEADMAN else "Староста",
        )
        self.payload["announcements"].insert(0, item)
        self.save()
        return item

    def list_polls(self) -> list[Poll]:
        return sorted(self.payload["polls"], key=lambda item: item.created_at, reverse=True)

    def create_poll(self, question: str, options: list[str]) -> Poll:
        clean_options = [item.strip() for item in options if item.strip()]
        if len(clean_options) < 2:
            raise ValueError("Нужно минимум 2 варианта ответа")
        poll = Poll(
            poll_id=self._next_poll_id(),
            question=question.strip(),
            options=[PollOption(text=item) for item in clean_options],
            created_by=self.get_profile().name,
        )
        self.payload["polls"].insert(0, poll)
        self.save()
        return poll

    def vote(self, poll_id: str, option_index: int) -> bool:
        poll = self.find_poll(poll_id)
        if poll is None:
            return False
        profile = self.get_profile()
        voter = f"{profile.name}:{profile.room}"
        if voter in poll.voters:
            return False
        if option_index < 0 or option_index >= len(poll.options):
            return False
        poll.options[option_index].votes += 1
        poll.voters.append(voter)
        self.save()
        return True

    def find_poll(self, poll_id: str) -> Poll | None:
        for poll in self.payload["polls"]:
            if poll.poll_id == poll_id:
                return poll
        return None

    def _next_issue_id(self) -> str:
        return f"issue-{len(self.payload['issues']) + 101}"

    def _next_announcement_id(self) -> str:
        return f"ann-{len(self.payload['announcements']) + 1:03d}"

    def _next_poll_id(self) -> str:
        return f"poll-{len(self.payload['polls']) + 201}"
