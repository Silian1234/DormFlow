from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from kivy.utils import platform


class ApiError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class DormFlowApiClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 7.0) -> None:
        self.base_url = normalize_base_url(base_url)
        self.token = token
        self.timeout = timeout

    def set_token(self, token: str | None) -> None:
        self.token = token

    def register(
        self,
        *,
        email: str,
        password: str,
        name: str,
        building: str,
        floor: str,
        room: str,
        headman_code: str = "",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/register",
            {
                "email": email,
                "password": password,
                "name": name,
                "building": building,
                "floor": floor,
                "room": room,
                "headman_code": headman_code or None,
            },
            auth=False,
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request("POST", "/auth/login", {"email": email, "password": password}, auth=False)

    def logout(self) -> None:
        self._request("POST", "/auth/logout")

    def state(self) -> dict[str, Any]:
        return self._request("GET", "/state")

    def create_issue(self, title: str, description: str, category: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/issues",
            {"title": title, "description": description, "category": category},
        )

    def advance_issue(self, issue_id: str) -> dict[str, Any]:
        return self._request("POST", f"/issues/{issue_id}/advance")

    def complete_duty(self, duty_id: str) -> dict[str, Any]:
        return self._request("POST", f"/duties/{duty_id}/complete")

    def create_duty(
        self,
        *,
        title: str,
        date_label: str,
        room_scope: str,
        checklist: list[str],
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/duties",
            {
                "title": title,
                "date_label": date_label,
                "room_scope": room_scope,
                "checklist": checklist,
            },
        )

    def create_announcement(self, title: str, body: str) -> dict[str, Any]:
        return self._request("POST", "/announcements", {"title": title, "body": body})

    def create_poll(self, question: str, options: list[str]) -> dict[str, Any]:
        return self._request("POST", "/polls", {"question": question, "options": options})

    def vote(self, poll_id: str, option_index: int) -> dict[str, Any]:
        return self._request("POST", f"/polls/{poll_id}/vote", {"option_index": option_index})

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        auth: bool = True,
    ) -> Any:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        if auth:
            if not self.token:
                raise ApiError(401, "Нужен вход в аккаунт")
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise ApiError(exc.code, _read_error_message(exc)) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise ApiError(0, _connection_error_message(self.base_url, exc)) from exc

        if not raw:
            return None
        return json.loads(raw)


def normalize_base_url(value: str) -> str:
    result = value.strip().rstrip("/")
    if not result:
        result = default_api_base_url()
    if not result.startswith(("http://", "https://")):
        result = f"http://{result}"
    return result


def default_api_base_url() -> str:
    if platform == "android":
        return "http://10.0.2.2:8765"
    return "http://127.0.0.1:8765"


def _connection_error_message(base_url: str, exc: BaseException) -> str:
    if platform == "android" and "10.0.2.2" in base_url:
        return (
            "Сервер недоступен. 10.0.2.2 работает только в Android Emulator. "
            "На реальном телефоне укажите LAN IP компьютера, например http://192.168.1.109:8765, "
            "или подключите USB debugging и выполните adb reverse tcp:8765 tcp:8765, затем используйте http://127.0.0.1:8765."
        )
    if platform == "android":
        return (
            f"Сервер недоступен: {exc}. Проверьте, что телефон и компьютер в одной сети, "
            "backend запущен с --host 0.0.0.0, а Windows Firewall пропускает порт 8765."
        )
    return f"Сервер недоступен: {exc}"


def _read_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8")
        data = json.loads(raw)
    except Exception:
        return f"HTTP {exc.code}"
    detail = data.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        messages = []
        for item in detail:
            if isinstance(item, dict):
                location = ".".join(str(part) for part in item.get("loc", []) if part != "body")
                message = item.get("msg") or item.get("type")
                if location and message:
                    messages.append(f"{location}: {message}")
                elif message:
                    messages.append(str(message))
            else:
                messages.append(str(item))
        if messages:
            return "; ".join(messages)
    if detail is not None:
        return str(detail)
    return f"HTTP {exc.code}"
