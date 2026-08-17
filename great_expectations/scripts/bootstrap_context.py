from __future__ import annotations

from pathlib import Path

from src.validation.gx_runner import bootstrap_context_directory


def main() -> int:
    bootstrap_context_directory(Path("great_expectations"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

