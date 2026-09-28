"""Uvicorn server entry point."""

from pathlib import Path

import uvicorn


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        import os
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def main() -> None:
    _load_dotenv()
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
