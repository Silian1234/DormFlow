from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def _prepare_kivy_home() -> None:
    writable_root = os.environ.get("ANDROID_PRIVATE")
    if not writable_root:
        return
    kivy_home = Path(writable_root) / ".kivy"
    kivy_home.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("KIVY_HOME", str(kivy_home))
    os.environ.setdefault("KIVY_NO_CONFIG", "1")


def _run_mobile_app() -> None:
    _prepare_kivy_home()

    from dormflow.app import create_app

    create_app().run()


def _run_backend(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Run DormFlow backend API.")
    parser.add_argument("--host", default=os.getenv("DORMFLOW_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DORMFLOW_PORT", "8765")))
    parser.add_argument("--database", default=os.getenv("DORMFLOW_DATABASE"))
    parser.add_argument("--headman-code", default=os.getenv("DORMFLOW_HEADMAN_CODE"))
    args = parser.parse_args(argv)

    backend_dir = ROOT_DIR / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        import uvicorn
        from dormflow_backend.app import create_app as create_backend_app
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Backend dependencies are not installed. Run: "
            "py -3.10 -m pip install -r backend\\requirements.txt"
        ) from exc

    database_path = Path(args.database) if args.database else None
    app = create_backend_app(database_path=database_path, headman_code=args.headman_code)
    uvicorn.run(app, host=args.host, port=args.port, reload=False)


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"backend", "server", "api", "--backend"}:
        _run_backend(args[1:])
        return
    _run_mobile_app()


if __name__ == "__main__":
    main()
