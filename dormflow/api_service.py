from __future__ import annotations

from dormflow.api_client import DormFlowApiClient
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


class RemoteDormFlowService:
    def __init__(self, client: DormFlowApiClient) -> None:
        self.client = client
        self.profile: UserProfile | None = None
        self.duties: list[Duty] = []
        self.issues: list[Issue] = []
        self.announcements: list[Announcement] = []
        self.polls: list[Poll] = []
        self.refresh()

    def refresh(self) -> None:
        state = self.client.state()
        self.profile = _profile_from_dict(state["profile"])
        self.duties = [_duty_from_dict(item) for item in state.get("duties", [])]
        self.issues = [_issue_from_dict(item) for item in state.get("issues", [])]
        self.announcements = [_announcement_from_dict(item) for item in state.get("announcements", [])]
        self.polls = [_poll_from_dict(item) for item in state.get("polls", [])]

    def save(self) -> None:
        return None

    def get_profile(self) -> UserProfile:
        if self.profile is None:
            self.refresh()
        return self.profile

    def switch_role(self, role: UserRole) -> None:
        raise PermissionError("Роль нельзя переключить на клиенте")

    def list_duties(self) -> list[Duty]:
        return sorted(self.duties, key=lambda item: item.date_label)

    def mark_duty_done(self, duty_id: str) -> bool:
        duty = _duty_from_dict(self.client.complete_duty(duty_id))
        self._replace_duty(duty)
        return True

    def create_duty(self, title: str, date_label: str, room_scope: str, checklist: list[str]) -> Duty:
        duty = _duty_from_dict(
            self.client.create_duty(
                title=title,
                date_label=date_label,
                room_scope=room_scope,
                checklist=checklist,
            )
        )
        self.duties.insert(0, duty)
        return duty

    def find_duty(self, duty_id: str) -> Duty | None:
        return next((item for item in self.duties if item.duty_id == duty_id), None)

    def list_issues(self) -> list[Issue]:
        return sorted(self.issues, key=lambda item: item.updated_at, reverse=True)

    def find_issue(self, issue_id: str) -> Issue | None:
        return next((item for item in self.issues if item.issue_id == issue_id), None)

    def create_issue(self, title: str, description: str, category: str) -> Issue:
        issue = _issue_from_dict(self.client.create_issue(title, description, category))
        self.issues.insert(0, issue)
        return issue

    def move_issue_status(self, issue_id: str) -> Issue | None:
        issue = _issue_from_dict(self.client.advance_issue(issue_id))
        self._replace_issue(issue)
        return issue

    def list_announcements(self) -> list[Announcement]:
        return sorted(self.announcements, key=lambda item: item.published_at, reverse=True)

    def create_announcement(self, title: str, body: str) -> Announcement:
        item = _announcement_from_dict(self.client.create_announcement(title, body))
        self.announcements.insert(0, item)
        return item

    def list_polls(self) -> list[Poll]:
        return sorted(self.polls, key=lambda item: item.created_at, reverse=True)

    def create_poll(self, question: str, options: list[str]) -> Poll:
        poll = _poll_from_dict(self.client.create_poll(question, options))
        self.polls.insert(0, poll)
        return poll

    def vote(self, poll_id: str, option_index: int) -> bool:
        poll = _poll_from_dict(self.client.vote(poll_id, option_index))
        self._replace_poll(poll)
        return True

    def find_poll(self, poll_id: str) -> Poll | None:
        return next((item for item in self.polls if item.poll_id == poll_id), None)

    def _replace_duty(self, duty: Duty) -> None:
        self.duties = [duty if item.duty_id == duty.duty_id else item for item in self.duties]

    def _replace_issue(self, issue: Issue) -> None:
        self.issues = [issue if item.issue_id == issue.issue_id else item for item in self.issues]

    def _replace_poll(self, poll: Poll) -> None:
        self.polls = [poll if item.poll_id == poll.poll_id else item for item in self.polls]


def _profile_from_dict(data: dict) -> UserProfile:
    return UserProfile(
        name=data.get("name", ""),
        building=data.get("building", ""),
        floor=data.get("floor", ""),
        room=data.get("room", ""),
        role=UserRole(data.get("role", UserRole.RESIDENT.value)),
        email=data.get("email", ""),
        user_id=data.get("user_id"),
    )


def _duty_from_dict(data: dict) -> Duty:
    return Duty(
        duty_id=data["duty_id"],
        title=data["title"],
        date_label=data["date_label"],
        room_scope=data["room_scope"],
        checklist=list(data.get("checklist", [])),
        status=DutyStatus(data.get("status", DutyStatus.PENDING.value)),
        completed_at=data.get("completed_at"),
    )


def _issue_from_dict(data: dict) -> Issue:
    return Issue(
        issue_id=data["issue_id"],
        title=data["title"],
        description=data["description"],
        category=data["category"],
        room_scope=data["room_scope"],
        created_by=data["created_by"],
        status=IssueStatus(data.get("status", IssueStatus.NEW.value)),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


def _announcement_from_dict(data: dict) -> Announcement:
    return Announcement(
        announcement_id=data["announcement_id"],
        title=data["title"],
        body=data["body"],
        author=data["author"],
        published_at=data.get("published_at", ""),
    )


def _poll_from_dict(data: dict) -> Poll:
    return Poll(
        poll_id=data["poll_id"],
        question=data["question"],
        options=[PollOption(text=item["text"], votes=int(item.get("votes", 0))) for item in data.get("options", [])],
        created_by=data["created_by"],
        created_at=data.get("created_at", ""),
        voters=list(data.get("voters", [])),
    )

