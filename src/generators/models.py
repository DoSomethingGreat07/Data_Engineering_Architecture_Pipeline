from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratedPaths:
    customers_csv: Path
    customers_json: Path
    accounts_csv: Path
    accounts_json: Path
    securities_csv: Path
    securities_json: Path
    transactions_csv: Path
    transactions_json: Path
    payments_csv: Path
    payments_json: Path
    trades_csv: Path
    trades_json: Path
    balances_csv: Path
    balances_json: Path
    ingest_ready_dir: Path
    stream_events_jsonl: Path
    malformed_stream_events_jsonl: Path
