from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

TIMESTAMP_PATTERN = re.compile(r"_(\d{8}T\d{6}Z)\.json$")
POSITIVE_TRANSACTION_TYPES = {"CREDIT", "REFUND"}


@dataclass(frozen=True)
class StagedDataset:
    dataset_name: str
    output_path: Path
    record_count: int


def load_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a top-level list")
    return [dict(record) for record in payload]


def extract_timestamp(path: Path) -> str:
    match = TIMESTAMP_PATTERN.search(path.name)
    if match is None:
        raise ValueError(f"unable to extract timestamp from {path.name}")
    return match.group(1)


def find_latest_dataset_file(source_dir: Path, dataset_name: str) -> Path | None:
    candidates = sorted(source_dir.glob(f"{dataset_name}_*.json"))
    if not candidates:
        return None
    return max(candidates, key=extract_timestamp)


def write_dataset(
    bronze_root: Path,
    dataset_name: str,
    timestamp: str,
    records: list[dict[str, Any]],
) -> StagedDataset:
    dataset_dir = bronze_root / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    output_path = dataset_dir / f"{dataset_name}_{timestamp}.json"
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return StagedDataset(
        dataset_name=dataset_name,
        output_path=output_path,
        record_count=len(records),
    )


def copy_dataset_file(source_path: Path, bronze_root: Path, dataset_name: str) -> StagedDataset:
    dataset_dir = bronze_root / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    output_path = dataset_dir / source_path.name
    shutil.copy2(source_path, output_path)
    return StagedDataset(
        dataset_name=dataset_name,
        output_path=output_path,
        record_count=len(load_json_records(source_path)),
    )


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def decimal_as_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def signed_transaction_amount(record: dict[str, Any]) -> Decimal:
    amount = Decimal(str(record["transaction_amount"]))
    transaction_type = str(record.get("transaction_type", "")).upper()
    if transaction_type in POSITIVE_TRANSACTION_TYPES:
        return amount
    return -amount


def derive_daily_account_balances(
    accounts: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_account: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in transactions:
        by_account[str(record["account_id"])].append(record)

    balances: list[dict[str, Any]] = []
    for account in accounts:
        account_id = str(account["account_id"])
        customer_id = str(account["customer_id"])
        currency_code = str(account["currency_code"])
        account_transactions = sorted(
            by_account.get(account_id, []),
            key=lambda item: parse_iso_datetime(str(item["event_timestamp"])),
        )
        current_balance = Decimal(str(account["current_balance"]))

        if not account_transactions:
            opened_at = parse_iso_datetime(str(account["opened_at"]))
            balances.append(
                {
                    "balance_id": f"{account_id}-{opened_at.date().isoformat()}",
                    "account_id": account_id,
                    "customer_id": customer_id,
                    "balance_date": opened_at.date().isoformat() + "T00:00:00Z",
                    "opening_balance": decimal_as_string(current_balance),
                    "closing_balance": decimal_as_string(current_balance),
                    "currency_code": currency_code,
                }
            )
            continue

        signed_total = sum(
            (signed_transaction_amount(record) for record in account_transactions),
            start=Decimal("0"),
        )
        running_opening = current_balance - signed_total
        grouped_by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in account_transactions:
            event_day = parse_iso_datetime(str(record["event_timestamp"])).date().isoformat()
            grouped_by_day[event_day].append(record)

        for event_day in sorted(grouped_by_day):
            daily_net = sum(
                (signed_transaction_amount(record) for record in grouped_by_day[event_day]),
                start=Decimal("0"),
            )
            closing_balance = running_opening + daily_net
            balances.append(
                {
                    "balance_id": f"{account_id}-{event_day}",
                    "account_id": account_id,
                    "customer_id": customer_id,
                    "balance_date": event_day + "T00:00:00Z",
                    "opening_balance": decimal_as_string(running_opening),
                    "closing_balance": decimal_as_string(closing_balance),
                    "currency_code": currency_code,
                }
            )
            running_opening = closing_balance
    return balances


def stage_plaid_batch_for_processing(
    canonical_root: Path,
    bronze_root: Path,
) -> list[StagedDataset]:
    plaid_dir = canonical_root / "plaid"
    alpha_vantage_dir = canonical_root / "alpha_vantage"

    customers_file = find_latest_dataset_file(plaid_dir, "customers")
    accounts_file = find_latest_dataset_file(plaid_dir, "accounts")
    transactions_file = find_latest_dataset_file(plaid_dir, "transactions")
    if customers_file is None or accounts_file is None or transactions_file is None:
        raise FileNotFoundError(
            "latest Plaid customers/accounts/transactions files were not found under "
            f"{plaid_dir}"
        )

    timestamp = extract_timestamp(transactions_file)
    staged = [
        copy_dataset_file(customers_file, bronze_root, "customers"),
        copy_dataset_file(accounts_file, bronze_root, "accounts"),
        copy_dataset_file(transactions_file, bronze_root, "transactions"),
    ]

    securities_file = find_latest_dataset_file(alpha_vantage_dir, "securities")
    if securities_file is not None:
        staged.append(copy_dataset_file(securities_file, bronze_root, "securities"))
    else:
        staged.append(write_dataset(bronze_root, "securities", timestamp, []))

    accounts = load_json_records(accounts_file)
    transactions = load_json_records(transactions_file)
    daily_balances = derive_daily_account_balances(accounts, transactions)
    staged.append(write_dataset(bronze_root, "daily_account_balances", timestamp, daily_balances))

    staged.append(write_dataset(bronze_root, "payments", timestamp, []))
    staged.append(write_dataset(bronze_root, "trades", timestamp, []))
    return staged
