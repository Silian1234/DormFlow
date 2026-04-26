from __future__ import annotations

import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from dormflow.api_client import _read_error_message, default_api_base_url
from dormflow.session import SessionStore


class ClientConfigTests(unittest.TestCase):
    def test_desktop_default_backend_port_is_dormflow_port(self):
        self.assertEqual(default_api_base_url(), "http://127.0.0.1:8765")

    def test_session_migrates_old_default_port(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.json"
            path.write_text(
                json.dumps({"base_url": "http://127.0.0.1:8000", "token": ""}),
                encoding="utf-8",
            )

            session = SessionStore(path).load()

        self.assertEqual(session["base_url"], "http://127.0.0.1:8765")

    def test_http_error_reads_fastapi_validation_detail(self):
        body = json.dumps(
            {
                "detail": [
                    {"loc": ["body", "email"], "msg": "Field required"},
                    {"loc": ["body", "password"], "msg": "String should have at least 6 characters"},
                ]
            }
        ).encode("utf-8")
        error = urllib.error.HTTPError(
            url="http://127.0.0.1:8765/auth/register",
            code=422,
            msg="Unprocessable Entity",
            hdrs={},
            fp=io.BytesIO(body),
        )

        message = _read_error_message(error)

        self.assertIn("email: Field required", message)
        self.assertIn("password: String should have at least 6 characters", message)


if __name__ == "__main__":
    unittest.main()
