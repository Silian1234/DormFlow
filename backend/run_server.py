from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dormflow_backend.app import create_app  # noqa: E402


app = create_app()


if __name__ == "__main__":
    host = os.getenv("DORMFLOW_HOST", "0.0.0.0")
    port = int(os.getenv("DORMFLOW_PORT", "8765"))
    uvicorn.run("run_server:app", host=host, port=port, reload=False)
