from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

try:
    from fastapi.testclient import TestClient
    from dormflow_backend.app import create_app
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(f"backend dependencies are not installed: {exc}") from exc


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        app = create_app(Path(self.tmp_dir.name) / "test.sqlite3", headman_code="SECRET")
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.tmp_dir.cleanup()

    def test_register_login_and_state(self):
        token = self._register("resident@example.com")
        response = self.client.get("/state", headers=self._auth(token))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"]["role"], "resident")
        self.assertGreaterEqual(len(payload["duties"]), 1)

        login = self.client.post(
            "/auth/login",
            json={"email": "resident@example.com", "password": "password1"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("token", login.json())

    def test_auth_rejects_bad_paths_and_logout_invalidates_session(self):
        token = self._register("resident@example.com")

        duplicate = self.client.post(
            "/auth/register",
            json={
                "email": "resident@example.com",
                "password": "password1",
                "name": "Duplicate",
                "building": "3",
                "floor": "4",
                "room": "418",
            },
        )
        self.assertEqual(duplicate.status_code, 409)

        wrong_password = self.client.post(
            "/auth/login",
            json={"email": "resident@example.com", "password": "wrong-password"},
        )
        self.assertEqual(wrong_password.status_code, 401)

        anonymous_state = self.client.get("/state")
        self.assertEqual(anonymous_state.status_code, 401)

        logout = self.client.post("/auth/logout", headers=self._auth(token))
        self.assertEqual(logout.status_code, 200)

        stale_session = self.client.get("/state", headers=self._auth(token))
        self.assertEqual(stale_session.status_code, 401)

    def test_resident_cannot_create_headman_content(self):
        token = self._register("resident@example.com")
        response = self.client.post(
            "/announcements",
            json={"title": "Тест", "body": "Текст"},
            headers=self._auth(token),
        )
        self.assertEqual(response.status_code, 403)

    def test_headman_can_create_duty_and_moderate_issue(self):
        token = self._register("headman@example.com", headman_code="SECRET")
        duty = self.client.post(
            "/duties",
            json={
                "title": "Дежурство",
                "date_label": "27 апреля, 19:00",
                "room_scope": "Этаж 4",
                "checklist": ["Кухня", "Мусор"],
            },
            headers=self._auth(token),
        )
        self.assertEqual(duty.status_code, 200)
        self.assertEqual(duty.json()["status"], "pending")

        state = self.client.get("/state", headers=self._auth(token)).json()
        issue_id = state["issues"][0]["issue_id"]
        moved = self.client.post(f"/issues/{issue_id}/advance", headers=self._auth(token))
        self.assertEqual(moved.status_code, 200)
        self.assertIn(moved.json()["status"], {"in_progress", "done"})

    def test_poll_vote_only_once_per_user(self):
        token = self._register("resident@example.com")
        state = self.client.get("/state", headers=self._auth(token)).json()
        poll_id = state["polls"][0]["poll_id"]
        first = self.client.post(
            f"/polls/{poll_id}/vote",
            json={"option_index": 0},
            headers=self._auth(token),
        )
        second = self.client.post(
            f"/polls/{poll_id}/vote",
            json={"option_index": 1},
            headers=self._auth(token),
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)

    def _register(self, email: str, headman_code: str = "") -> str:
        response = self.client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password1",
                "name": "Иван Иванов",
                "building": "Корпус 3",
                "floor": "4",
                "room": "418",
                "headman_code": headman_code or None,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["token"]

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    unittest.main()
