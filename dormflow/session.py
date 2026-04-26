from __future__ import annotations

import json
from pathlib import Path

from dormflow.api_client import default_api_base_url, normalize_base_url


LEGACY_DEFAULT_BASE_URLS = {
    "http://10.0.2.2:8000",
    "http://127.0.0.1:8000",
}


class SessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {"base_url": default_api_base_url(), "token": ""}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"base_url": default_api_base_url(), "token": ""}
        base_url = normalize_base_url(data.get("base_url", default_api_base_url()))
        if base_url in LEGACY_DEFAULT_BASE_URLS:
            base_url = default_api_base_url()
        return {
            "base_url": base_url,
            "token": data.get("token", ""),
        }

    def save(self, base_url: str, token: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"base_url": normalize_base_url(base_url), "token": token}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return
