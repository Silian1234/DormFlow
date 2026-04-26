from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from dormflow.models import DutyStatus, IssueStatus, UserRole

from .database import (
    Database,
    announcement_to_dict,
    duty_to_dict,
    issue_to_dict,
    poll_to_dict,
    user_to_dict,
)
from .security import hash_password, make_token, verify_password


DEFAULT_HEADMAN_CODE = "HEADMAN-2026"


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    building: str
    floor: str
    room: str
    headman_code: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class IssueCreateRequest(BaseModel):
    title: str
    description: str
    category: str = "Другое"


class AnnouncementCreateRequest(BaseModel):
    title: str
    body: str


class PollCreateRequest(BaseModel):
    question: str
    options: list[str]


class PollVoteRequest(BaseModel):
    option_index: int


class DutyCreateRequest(BaseModel):
    title: str
    date_label: str
    room_scope: str
    checklist: list[str]


def create_app(
    database_path: str | Path | None = None,
    headman_code: str | None = None,
) -> FastAPI:
    data_path = Path(
        database_path
        or os.getenv("DORMFLOW_DATABASE")
        or Path(__file__).resolve().parents[1] / "data" / "dormflow.sqlite3"
    )
    db = Database(data_path)
    db.initialize()

    app = FastAPI(title="DormFlow API", version="1.0.0")
    app.state.database = db
    app.state.headman_code = headman_code or os.getenv("DORMFLOW_HEADMAN_CODE", DEFAULT_HEADMAN_CODE)

    def get_db() -> Database:
        return app.state.database

    def current_user(
        authorization: Annotated[str | None, Header()] = None,
        database: Database = Depends(get_db),
    ) -> sqlite3.Row:
        token = _extract_bearer_token(authorization)
        with database.session() as connection:
            row = connection.execute(
                """
                SELECT users.*
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия недействительна")
        return row

    def require_headman(user: sqlite3.Row = Depends(current_user)) -> sqlite3.Row:
        if user["role"] != UserRole.HEADMAN.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступно только старосте")
        return user

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "dormflow"}

    @app.post("/auth/register")
    def register(payload: RegisterRequest, database: Database = Depends(get_db)) -> dict[str, Any]:
        email = _normalize_email(payload.email)
        _validate_required(
            {
                "email": email,
                "password": payload.password,
                "name": payload.name,
                "building": payload.building,
                "floor": payload.floor,
                "room": payload.room,
            }
        )
        if len(payload.password) < 6:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Пароль должен быть от 6 символов")

        role = UserRole.RESIDENT
        if payload.headman_code:
            if payload.headman_code.strip() != app.state.headman_code:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неверный код старосты")
            role = UserRole.HEADMAN

        with database.session() as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        email, password_hash, name, building, floor, room, role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        hash_password(payload.password),
                        payload.name.strip(),
                        payload.building.strip(),
                        payload.floor.strip(),
                        payload.room.strip(),
                        role.value,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует") from exc
            user = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
            token = _create_session(connection, user["id"])
        return {"token": token, "user": user_to_dict(user)}

    @app.post("/auth/login")
    def login(payload: LoginRequest, database: Database = Depends(get_db)) -> dict[str, Any]:
        email = _normalize_email(payload.email)
        with database.session() as connection:
            user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user is None or not verify_password(payload.password, user["password_hash"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
            token = _create_session(connection, user["id"])
        return {"token": token, "user": user_to_dict(user)}

    @app.post("/auth/logout")
    def logout(
        authorization: Annotated[str | None, Header()] = None,
        database: Database = Depends(get_db),
    ) -> dict[str, bool]:
        token = _extract_bearer_token(authorization)
        with database.session() as connection:
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return {"ok": True}

    @app.get("/me")
    def me(user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
        return user_to_dict(user)

    @app.get("/state")
    def state(
        user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        with database.session() as connection:
            return {
                "profile": user_to_dict(user),
                "duties": [
                    duty_to_dict(row)
                    for row in connection.execute("SELECT * FROM duties ORDER BY date_label").fetchall()
                ],
                "issues": [
                    issue_to_dict(row)
                    for row in connection.execute("SELECT * FROM issues ORDER BY updated_at DESC").fetchall()
                ],
                "announcements": [
                    announcement_to_dict(row)
                    for row in connection.execute("SELECT * FROM announcements ORDER BY published_at DESC").fetchall()
                ],
                "polls": [
                    poll_to_dict(row)
                    for row in connection.execute("SELECT * FROM polls ORDER BY created_at DESC").fetchall()
                ],
            }

    @app.get("/duties")
    def list_duties(
        _user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> list[dict[str, Any]]:
        with database.session() as connection:
            return [duty_to_dict(row) for row in connection.execute("SELECT * FROM duties ORDER BY date_label")]

    @app.post("/duties")
    def create_duty(
        payload: DutyCreateRequest,
        _user: sqlite3.Row = Depends(require_headman),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        checklist = [item.strip() for item in payload.checklist if item.strip()]
        _validate_required(
            {
                "title": payload.title,
                "date_label": payload.date_label,
                "room_scope": payload.room_scope,
            }
        )
        if not checklist:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Нужен хотя бы один пункт чек-листа")
        duty_id = f"duty-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        with database.session() as connection:
            connection.execute(
                """
                INSERT INTO duties (
                    duty_id, title, date_label, room_scope, checklist_json, status, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    duty_id,
                    payload.title.strip(),
                    payload.date_label.strip(),
                    payload.room_scope.strip(),
                    json.dumps(checklist, ensure_ascii=False),
                    DutyStatus.PENDING.value,
                ),
            )
            row = connection.execute("SELECT * FROM duties WHERE duty_id = ?", (duty_id,)).fetchone()
        return duty_to_dict(row)

    @app.post("/duties/{duty_id}/complete")
    def complete_duty(
        duty_id: str,
        _user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        with database.session() as connection:
            row = connection.execute("SELECT * FROM duties WHERE duty_id = ?", (duty_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Дежурство не найдено")
            connection.execute(
                "UPDATE duties SET status = ?, completed_at = ? WHERE duty_id = ?",
                (DutyStatus.DONE.value, _now(), duty_id),
            )
            row = connection.execute("SELECT * FROM duties WHERE duty_id = ?", (duty_id,)).fetchone()
        return duty_to_dict(row)

    @app.get("/issues")
    def list_issues(
        _user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> list[dict[str, Any]]:
        with database.session() as connection:
            return [issue_to_dict(row) for row in connection.execute("SELECT * FROM issues ORDER BY updated_at DESC")]

    @app.post("/issues")
    def create_issue(
        payload: IssueCreateRequest,
        user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        _validate_required({"title": payload.title, "description": payload.description})
        issue_id = f"issue-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        now = _now()
        with database.session() as connection:
            connection.execute(
                """
                INSERT INTO issues (
                    issue_id, title, description, category, room_scope, created_by,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    issue_id,
                    payload.title.strip(),
                    payload.description.strip(),
                    payload.category.strip() or "Другое",
                    f"Этаж {user['floor']}, комната {user['room']}",
                    user["name"],
                    IssueStatus.NEW.value,
                    now,
                    now,
                ),
            )
            row = connection.execute("SELECT * FROM issues WHERE issue_id = ?", (issue_id,)).fetchone()
        return issue_to_dict(row)

    @app.post("/issues/{issue_id}/advance")
    def advance_issue(
        issue_id: str,
        _user: sqlite3.Row = Depends(require_headman),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        with database.session() as connection:
            row = connection.execute("SELECT * FROM issues WHERE issue_id = ?", (issue_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
            current_status = IssueStatus(row["status"])
            next_status = {
                IssueStatus.NEW: IssueStatus.IN_PROGRESS,
                IssueStatus.IN_PROGRESS: IssueStatus.DONE,
                IssueStatus.DONE: IssueStatus.DONE,
            }[current_status]
            connection.execute(
                "UPDATE issues SET status = ?, updated_at = ? WHERE issue_id = ?",
                (next_status.value, _now(), issue_id),
            )
            row = connection.execute("SELECT * FROM issues WHERE issue_id = ?", (issue_id,)).fetchone()
        return issue_to_dict(row)

    @app.get("/announcements")
    def list_announcements(
        _user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> list[dict[str, Any]]:
        with database.session() as connection:
            return [
                announcement_to_dict(row)
                for row in connection.execute("SELECT * FROM announcements ORDER BY published_at DESC")
            ]

    @app.post("/announcements")
    def create_announcement(
        payload: AnnouncementCreateRequest,
        user: sqlite3.Row = Depends(require_headman),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        _validate_required({"title": payload.title, "body": payload.body})
        announcement_id = f"ann-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        with database.session() as connection:
            connection.execute(
                """
                INSERT INTO announcements (
                    announcement_id, title, body, author, published_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (announcement_id, payload.title.strip(), payload.body.strip(), user["name"], _now()),
            )
            row = connection.execute(
                "SELECT * FROM announcements WHERE announcement_id = ?",
                (announcement_id,),
            ).fetchone()
        return announcement_to_dict(row)

    @app.get("/polls")
    def list_polls(
        _user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> list[dict[str, Any]]:
        with database.session() as connection:
            return [poll_to_dict(row) for row in connection.execute("SELECT * FROM polls ORDER BY created_at DESC")]

    @app.post("/polls")
    def create_poll(
        payload: PollCreateRequest,
        user: sqlite3.Row = Depends(require_headman),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        options = [item.strip() for item in payload.options if item.strip()]
        _validate_required({"question": payload.question})
        if len(options) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Нужно минимум 2 варианта ответа")
        poll_id = f"poll-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        with database.session() as connection:
            connection.execute(
                """
                INSERT INTO polls (
                    poll_id, question, options_json, created_by, created_at, voters_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    poll_id,
                    payload.question.strip(),
                    json.dumps([{"text": item, "votes": 0} for item in options], ensure_ascii=False),
                    user["name"],
                    _now(),
                    json.dumps([], ensure_ascii=False),
                ),
            )
            row = connection.execute("SELECT * FROM polls WHERE poll_id = ?", (poll_id,)).fetchone()
        return poll_to_dict(row)

    @app.post("/polls/{poll_id}/vote")
    def vote(
        poll_id: str,
        payload: PollVoteRequest,
        user: sqlite3.Row = Depends(current_user),
        database: Database = Depends(get_db),
    ) -> dict[str, Any]:
        with database.session() as connection:
            row = connection.execute("SELECT * FROM polls WHERE poll_id = ?", (poll_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Голосование не найдено")
            poll = poll_to_dict(row)
            if payload.option_index < 0 or payload.option_index >= len(poll["options"]):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Некорректный вариант ответа")
            voter = str(user["id"])
            if voter in poll["voters"]:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Голос уже отдан")
            poll["options"][payload.option_index]["votes"] += 1
            poll["voters"].append(voter)
            connection.execute(
                "UPDATE polls SET options_json = ?, voters_json = ? WHERE poll_id = ?",
                (
                    json.dumps(poll["options"], ensure_ascii=False),
                    json.dumps(poll["voters"], ensure_ascii=False),
                    poll_id,
                ),
            )
            row = connection.execute("SELECT * FROM polls WHERE poll_id = ?", (poll_id,)).fetchone()
        return poll_to_dict(row)

    return app


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нужна авторизация")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нужна авторизация")
    return token


def _create_session(connection: sqlite3.Connection, user_id: int) -> str:
    token = make_token()
    connection.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    return token


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_required(values: dict[str, str]) -> None:
    missing = [key for key, value in values.items() if not value or not value.strip()]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Заполните поля: {', '.join(missing)}",
        )


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

