from __future__ import annotations

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


def default_profile() -> UserProfile:
    return UserProfile(
        name="Иван Иванов",
        building="Корпус 3",
        floor="4",
        room="418",
        role=UserRole.RESIDENT,
    )


def default_duties() -> list[Duty]:
    return [
        Duty(
            duty_id="duty-001",
            title="Дежурство по кухне",
            date_label="24 апреля, 19:00-21:00",
            room_scope="Этаж 4",
            checklist=[
                "Протереть столы",
                "Проверить мусорные контейнеры",
                "Убрать плиту",
            ],
        ),
        Duty(
            duty_id="duty-002",
            title="Дежурство по коридору",
            date_label="27 апреля, 19:00-21:00",
            room_scope="Этаж 4",
            checklist=[
                "Протереть перила",
                "Проверить освещение",
                "Влажная уборка пола",
            ],
        ),
        Duty(
            duty_id="duty-003",
            title="Дежурство по санузлу",
            date_label="20 апреля, 19:00-21:00",
            room_scope="Этаж 4",
            checklist=[
                "Проверить чистоту кабинок",
                "Проверить расходники",
            ],
            status=DutyStatus.DONE,
            completed_at="2026-04-20T21:04:00",
        ),
    ]


def default_issues() -> list[Issue]:
    return [
        Issue(
            issue_id="issue-101",
            title="Не работает душ в кабинке №2",
            description="Постоянно течет холодная вода, горячая не включается.",
            category="Сантехника",
            room_scope="Этаж 4",
            created_by="Иван Иванов",
            status=IssueStatus.IN_PROGRESS,
        ),
        Issue(
            issue_id="issue-102",
            title="Перегорела лампа в коридоре",
            description="На участке между 412 и 414 комнатами темно.",
            category="Электрика",
            room_scope="Этаж 4",
            created_by="Мария Петрова",
            status=IssueStatus.NEW,
        ),
    ]


def default_announcements() -> list[Announcement]:
    return [
        Announcement(
            announcement_id="ann-001",
            title="Отключение воды",
            body="25 апреля с 14:00 до 18:00 на этаже будет отключена вода.",
            author="Комендант",
        ),
        Announcement(
            announcement_id="ann-002",
            title="Проверка пожарной безопасности",
            body="Сегодня в 20:30 пройдет обход и проверка путей эвакуации.",
            author="Староста 4 этажа",
        ),
    ]


def default_polls() -> list[Poll]:
    return [
        Poll(
            poll_id="poll-201",
            question="Нужен ли кулер в общей кухне?",
            options=[
                PollOption("Да"),
                PollOption("Нет"),
                PollOption("Нужен, но после сессии"),
            ],
            created_by="Староста 4 этажа",
        )
    ]

