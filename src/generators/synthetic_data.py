from __future__ import annotations

import csv
import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from random import Random
from typing import Any

from src.common.config import GenerationConfig
from src.common.constants import (
    COUNTRY_CODES,
    INVALID_CURRENCY_CODE,
    MERCHANT_CATEGORIES,
    SECURITY_TYPES,
    VALID_CURRENCY_CODES,
    VALID_PAYMENT_STATUSES,
    VALID_TRADE_SIDES,
    VALID_TRANSACTION_STATUSES,
    VALID_TRANSACTION_TYPES,
)
from src.generators.models import GeneratedPaths

LOGGER = logging.getLogger(__name__)
BatchDatasetMap = dict[str, list[dict[str, Any]]]


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _isoformat(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return _isoformat(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    raise TypeError(f"Unsupported type: {type(value)!r}")


class FinancialDataGenerator:
    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.random = Random(config.seed)
        self.base_time = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)

    def generate_all(self) -> tuple[BatchDatasetMap, list[dict[str, Any]], list[str]]:
        customers = self._generate_customers()
        accounts = self._generate_accounts(customers)
        securities = self._generate_securities()
        transactions = self._generate_transactions(customers, accounts)
        payments = self._generate_payments(customers, accounts)
        trades = self._generate_trades(customers, accounts, securities)
        balances = self._generate_daily_balances(customers, accounts)
        stream_events = self._generate_stream_events(transactions, payments, trades)
        malformed_events = self._generate_malformed_events()
        batch_datasets: BatchDatasetMap = {
            "customers": customers,
            "accounts": accounts,
            "securities": securities,
            "transactions": transactions,
            "payments": payments,
            "trades": trades,
            "daily_account_balances": balances,
        }
        return batch_datasets, stream_events, malformed_events

    def _generate_customers(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for index in range(self.config.customers):
            created_at = self.base_time - timedelta(days=self.random.randint(30, 3650))
            customer_id = f"CUST-{index + 1:05d}"
            records.append(
                {
                    "customer_id": customer_id,
                    "full_name": f"Customer {index + 1}",
                    "email": f"customer{index + 1}@example.com",
                    "country_code": self.random.choice(COUNTRY_CODES),
                    "risk_score": self.random.randint(1, 99),
                    "created_at": created_at,
                }
            )
        return records

    def _generate_accounts(self, customers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        account_index = 1
        for customer in customers:
            account_count = self.random.randint(
                self.config.accounts_per_customer.min,
                self.config.accounts_per_customer.max,
            )
            for _ in range(account_count):
                opened_at = self.base_time - timedelta(days=self.random.randint(30, 1825))
                records.append(
                    {
                        "account_id": f"ACCT-{account_index:06d}",
                        "customer_id": customer["customer_id"],
                        "account_type": self.random.choice(["CHECKING", "SAVINGS", "BROKERAGE"]),
                        "currency_code": self.config.base_currency,
                        "current_balance": _money(self.random.uniform(250.0, 250000.0)),
                        "opened_at": opened_at,
                        "status": self.random.choice(["OPEN", "OPEN", "OPEN", "SUSPENDED"]),
                    }
                )
                account_index += 1
        return records

    def _generate_securities(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for index in range(self.config.securities):
            ticker = f"SEC{index + 1:03d}"
            records.append(
                {
                    "security_id": f"SECURITY-{index + 1:05d}",
                    "ticker": ticker,
                    "security_name": f"Synthetic {ticker}",
                    "security_type": self.random.choice(SECURITY_TYPES),
                    "exchange_code": self.random.choice(["NYSE", "NASDAQ", "CBOE"]),
                    "currency_code": self.config.base_currency,
                }
            )
        return records

    def _generate_transactions(
        self, customers: list[dict[str, Any]], accounts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for index in range(self.config.transactions):
            customer, account = self._pick_customer_account(customers, accounts)
            event_time = self.base_time - timedelta(minutes=self.random.randint(1, 60 * 24 * 30))
            record = {
                "transaction_id": f"TXN-{index + 1:07d}",
                "account_id": account["account_id"],
                "customer_id": customer["customer_id"],
                "transaction_type": self.random.choice(list(VALID_TRANSACTION_TYPES)),
                "transaction_amount": _money(self.random.uniform(5.0, 15000.0)),
                "currency_code": self.random.choice(list(VALID_CURRENCY_CODES)),
                "transaction_status": self.random.choice(list(VALID_TRANSACTION_STATUSES)),
                "event_timestamp": event_time,
                "processing_timestamp": event_time + timedelta(minutes=self.random.randint(1, 60)),
                "merchant_category": self.random.choice(MERCHANT_CATEGORIES),
                "country_code": customer["country_code"],
                "risk_score": self.random.randint(0, 100),
            }
            records.append(record)
        return self._inject_batch_anomalies(
            records,
            id_field="transaction_id",
            amount_field="transaction_amount",
        )

    def _generate_payments(
        self, customers: list[dict[str, Any]], accounts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for index in range(self.config.payments):
            customer, account = self._pick_customer_account(customers, accounts)
            counterparty = self.random.choice(accounts)
            event_time = self.base_time - timedelta(minutes=self.random.randint(1, 60 * 24 * 7))
            record = {
                "payment_id": f"PAY-{index + 1:07d}",
                "account_id": account["account_id"],
                "customer_id": customer["customer_id"],
                "transaction_amount": _money(self.random.uniform(10.0, 50000.0)),
                "currency_code": self.random.choice(list(VALID_CURRENCY_CODES)),
                "transaction_status": self.random.choice(list(VALID_PAYMENT_STATUSES)),
                "event_timestamp": event_time,
                "processing_timestamp": event_time + timedelta(minutes=self.random.randint(1, 45)),
                "counterparty_account_id": counterparty["account_id"],
                "country_code": customer["country_code"],
                "risk_score": self.random.randint(0, 100),
            }
            records.append(record)
        return self._inject_batch_anomalies(
            records,
            id_field="payment_id",
            amount_field="transaction_amount",
        )

    def _generate_trades(
        self,
        customers: list[dict[str, Any]],
        accounts: list[dict[str, Any]],
        securities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for index in range(self.config.trades):
            customer, account = self._pick_customer_account(customers, accounts)
            security = self.random.choice(securities)
            quantity = _money(self.random.uniform(1.0, 1500.0))
            price = _money(self.random.uniform(12.0, 500.0))
            event_time = self.base_time - timedelta(minutes=self.random.randint(1, 60 * 24 * 14))
            record = {
                "trade_id": f"TRD-{index + 1:07d}",
                "account_id": account["account_id"],
                "customer_id": customer["customer_id"],
                "security_id": security["security_id"],
                "quantity": quantity,
                "price": price,
                "transaction_amount": _money(float(quantity * price)),
                "currency_code": security["currency_code"],
                "side": self.random.choice(list(VALID_TRADE_SIDES)),
                "transaction_status": self.random.choice(list(VALID_TRANSACTION_STATUSES)),
                "event_timestamp": event_time,
                "processing_timestamp": event_time + timedelta(minutes=self.random.randint(1, 30)),
                "country_code": customer["country_code"],
                "risk_score": self.random.randint(0, 100),
            }
            records.append(record)
        return self._inject_batch_anomalies(
            records,
            id_field="trade_id",
            amount_field="transaction_amount",
        )

    def _generate_daily_balances(
        self, customers: list[dict[str, Any]], accounts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        index = 1
        customer_lookup = {customer["customer_id"]: customer for customer in customers}
        for account in accounts:
            customer = customer_lookup[account["customer_id"]]
            opening = Decimal(account["current_balance"])
            for day_offset in range(self.config.daily_balances_days):
                balance_date = self.base_time - timedelta(days=day_offset)
                delta = _money(self.random.uniform(-500.0, 750.0))
                closing = opening + delta
                records.append(
                    {
                        "balance_id": f"BAL-{index:08d}",
                        "account_id": account["account_id"],
                        "customer_id": customer["customer_id"],
                        "balance_date": balance_date,
                        "opening_balance": opening,
                        "closing_balance": closing,
                        "currency_code": account["currency_code"],
                    }
                )
                opening = closing
                index += 1
        return records

    def _generate_stream_events(
        self,
        transactions: list[dict[str, Any]],
        payments: list[dict[str, Any]],
        trades: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        source_events = (
            [{"event_type": "transaction", **record} for record in transactions]
            + [{"event_type": "payment", **record} for record in payments]
            + [{"event_type": "trade", **record} for record in trades]
        )
        self.random.shuffle(source_events)
        events: list[dict[str, Any]] = []
        for index in range(self.config.stream_events):
            source = source_events[index % len(source_events)].copy()
            source["event_id"] = f"EVT-{index + 1:08d}"
            source["partition_key"] = source.get("account_id", "unknown")
            source["processing_timestamp"] = self.base_time + timedelta(seconds=index)
            if index < max(1, int(self.config.stream_events * self.config.late_event_ratio)):
                source["event_timestamp"] = source["event_timestamp"] - timedelta(days=3)
                source["late_arrival_flag"] = True
            else:
                source["late_arrival_flag"] = False
            events.append(source)
        duplicate_count = max(1, int(self.config.stream_events * self.config.duplicate_ratio))
        for index in range(duplicate_count):
            duplicate = events[index].copy()
            duplicate["duplicate_flag"] = True
            events.append(duplicate)
        invalid_count = max(1, int(self.config.stream_events * self.config.invalid_ratio))
        for index in range(invalid_count):
            target = events[index]
            target["currency_code"] = INVALID_CURRENCY_CODE
            target["risk_score"] = 999
        return events

    def _generate_malformed_events(self) -> list[str]:
        return [
            '{"event_id":"BROKEN-1","account_id":"ACCT-1"',
            "not-json-at-all",
            '{"event_type":"payment","missing_closing":true',
            '{"event_id":null,"event_type":"trade"}',
            '{"event_id":"BROKEN-5","event_type":"transaction","transaction_amount":"abc"}',
        ][: self.config.malformed_count]

    def _inject_batch_anomalies(
        self, records: list[dict[str, Any]], id_field: str, amount_field: str
    ) -> list[dict[str, Any]]:
        duplicate_count = max(1, int(len(records) * self.config.duplicate_ratio))
        invalid_count = max(1, int(len(records) * self.config.invalid_ratio))
        for index in range(duplicate_count):
            duplicate = records[index].copy()
            records.append(duplicate)
        for index in range(invalid_count):
            target = records[index]
            if index % 4 == 0:
                target[id_field] = None
            elif index % 4 == 1:
                target["currency_code"] = INVALID_CURRENCY_CODE
            elif index % 4 == 2:
                target[amount_field] = _money(-1 * abs(float(target[amount_field])))
            else:
                target["risk_score"] = 150
        return records

    def _pick_customer_account(
        self, customers: list[dict[str, Any]], accounts: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        account = self.random.choice(accounts)
        customer = next(
            customer for customer in customers if customer["customer_id"] == account["customer_id"]
        )
        return customer, account


def write_datasets(
    output_dir: str | Path,
    batch_datasets: BatchDatasetMap,
    stream_events: list[dict[str, Any]],
    malformed_stream_events: list[str],
) -> GeneratedPaths:
    base_dir = Path(output_dir)
    batch_dir = base_dir / "batch"
    ingest_ready_dir = batch_dir / "ingest_ready"
    streaming_dir = base_dir / "streaming"
    batch_dir.mkdir(parents=True, exist_ok=True)
    ingest_ready_dir.mkdir(parents=True, exist_ok=True)
    streaming_dir.mkdir(parents=True, exist_ok=True)

    paths = GeneratedPaths(
        customers_csv=batch_dir / "customers.csv",
        customers_json=batch_dir / "customers.json",
        accounts_csv=batch_dir / "accounts.csv",
        accounts_json=batch_dir / "accounts.json",
        securities_csv=batch_dir / "securities.csv",
        securities_json=batch_dir / "securities.json",
        transactions_csv=batch_dir / "transactions.csv",
        transactions_json=batch_dir / "transactions.json",
        payments_csv=batch_dir / "payments.csv",
        payments_json=batch_dir / "payments.json",
        trades_csv=batch_dir / "trades.csv",
        trades_json=batch_dir / "trades.json",
        balances_csv=batch_dir / "daily_account_balances.csv",
        balances_json=batch_dir / "daily_account_balances.json",
        ingest_ready_dir=ingest_ready_dir,
        stream_events_jsonl=streaming_dir / "events.jsonl",
        malformed_stream_events_jsonl=streaming_dir / "malformed_events.jsonl",
    )

    batch_mapping = {
        "customers": (paths.customers_csv, paths.customers_json),
        "accounts": (paths.accounts_csv, paths.accounts_json),
        "securities": (paths.securities_csv, paths.securities_json),
        "transactions": (paths.transactions_csv, paths.transactions_json),
        "payments": (paths.payments_csv, paths.payments_json),
        "trades": (paths.trades_csv, paths.trades_json),
        "daily_account_balances": (paths.balances_csv, paths.balances_json),
    }
    for dataset_name, (csv_path, json_path) in batch_mapping.items():
        rows = batch_datasets[dataset_name]
        _write_csv(csv_path, rows)
        _write_json(json_path, rows)
        timestamped_csv = ingest_ready_dir / f"{dataset_name}_20260815T120000Z.csv"
        timestamped_json = ingest_ready_dir / f"{dataset_name}_20260815T120000Z.json"
        _write_csv(timestamped_csv, rows)
        _write_json(timestamped_json, rows)
        LOGGER.info("wrote batch dataset", extra={"dataset": dataset_name, "rows": len(rows)})

    _write_jsonl(paths.stream_events_jsonl, stream_events)
    _write_text_lines(paths.malformed_stream_events_jsonl, malformed_stream_events)
    return paths


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: _json_default(value) if isinstance(value, datetime | Decimal) else value
                    for key, value in row.items()
                }
            )


def _write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, default=_json_default, indent=2)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=_json_default))
            handle.write("\n")


def _write_text_lines(path: Path, rows: list[str]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row)
            handle.write("\n")
