from __future__ import annotations

from pathlib import Path

from src.batch_producer.validation import FILENAME_PATTERN, VALID_BATCH_DATASETS


def discover_batch_files(
    root_dir: str | Path,
    *,
    latest_only: bool = False,
) -> list[Path]:
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"batch input directory not found: {root}")

    matched: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        match = FILENAME_PATTERN.match(path.name)
        if match is None:
            continue
        if match.group("dataset") not in VALID_BATCH_DATASETS:
            continue
        matched.append(path)

    if not latest_only:
        return matched

    latest_by_dataset: dict[str, Path] = {}
    for path in matched:
        dataset = path.name.split("_", 1)[0]
        current = latest_by_dataset.get(dataset)
        if current is None or path.name > current.name:
            latest_by_dataset[dataset] = path
    return sorted(latest_by_dataset.values(), key=lambda item: item.name)
