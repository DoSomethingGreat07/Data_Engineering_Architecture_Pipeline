from __future__ import annotations

from pathlib import Path


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    loaded: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#") or "=" not in candidate:
            continue
        key, value = candidate.split("=", 1)
        loaded[key.strip()] = _strip_optional_quotes(value.strip())
    return loaded


def apply_env_overrides(path: str | Path = ".env") -> None:
    import os

    for key, value in load_env_file(path).items():
        os.environ.setdefault(key, value)


def _strip_optional_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
