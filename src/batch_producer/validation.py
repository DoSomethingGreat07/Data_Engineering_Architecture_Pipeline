from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

VALID_BATCH_DATASETS = {
    "customers",
    "accounts",
    "securities",
    "transactions",
    "payments",
    "trades",
    "daily_account_balances",
}
FILENAME_PATTERN = re.compile(
    r"^(?P<dataset>[a-z_]+)_(?P<timestamp>\d{8}T\d{6}Z)\.(?P<extension>csv|json)$"
)


def validate_batch_filename(path: str | Path) -> tuple[str, str]:
    file_path = Path(path)
    match = FILENAME_PATTERN.match(file_path.name)
    if match is None:
        raise ValueError(
            "batch filenames must follow <dataset>_YYYYMMDDTHHMMSSZ.<csv|json>"
        )
    dataset_name = match.group("dataset")
    extension = match.group("extension")
    if dataset_name not in VALID_BATCH_DATASETS:
        raise ValueError(f"unsupported dataset name: {dataset_name}")
    return dataset_name, extension


def load_records(path: str | Path, source_format: str) -> list[dict[str, Any]]:
    file_path = Path(path)
    if source_format == "csv":
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if source_format == "json":
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            raise ValueError("json batch files must contain a top-level list")
        return [dict(row) for row in payload]
    raise ValueError(f"unsupported source format: {source_format}")


def validate_required_structure(dataset_name: str, records: list[dict[str, Any]]) -> int:
    if not records:
        raise ValueError(f"{dataset_name} batch file is empty")
    if any(not isinstance(record, dict) for record in records):
        raise ValueError(f"{dataset_name} batch file contains non-object records")
    return len(records)


def compute_file_checksum(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()

