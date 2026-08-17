import json
from pathlib import Path

from src.batch_preparation.plaid_bronze_stage import (
    derive_daily_account_balances,
    stage_plaid_batch_for_processing,
)


def test_derive_daily_account_balances_backfills_from_current_balance() -> None:
    accounts = [
        {
            "account_id": "acct-1",
            "customer_id": "cust-1",
            "currency_code": "USD",
            "current_balance": "200.00",
            "opened_at": "2026-08-01T00:00:00Z",
        }
    ]
    transactions = [
        {
            "account_id": "acct-1",
            "customer_id": "cust-1",
            "transaction_type": "DEBIT",
            "transaction_amount": "20.00",
            "event_timestamp": "2026-08-10T12:00:00Z",
        },
        {
            "account_id": "acct-1",
            "customer_id": "cust-1",
            "transaction_type": "CREDIT",
            "transaction_amount": "50.00",
            "event_timestamp": "2026-08-11T09:00:00Z",
        },
    ]

    balances = derive_daily_account_balances(accounts, transactions)

    assert balances == [
        {
            "balance_id": "acct-1-2026-08-10",
            "account_id": "acct-1",
            "customer_id": "cust-1",
            "balance_date": "2026-08-10T00:00:00Z",
            "opening_balance": "170.00",
            "closing_balance": "150.00",
            "currency_code": "USD",
        },
        {
            "balance_id": "acct-1-2026-08-11",
            "account_id": "acct-1",
            "customer_id": "cust-1",
            "balance_date": "2026-08-11T00:00:00Z",
            "opening_balance": "150.00",
            "closing_balance": "200.00",
            "currency_code": "USD",
        },
    ]


def test_stage_plaid_batch_for_processing_creates_full_bronze_layout(tmp_path: Path) -> None:
    canonical_root = tmp_path / "canonical"
    plaid_dir = canonical_root / "plaid"
    plaid_dir.mkdir(parents=True)
    bronze_root = tmp_path / "bronze"

    (plaid_dir / "customers_20260816T054139Z.json").write_text(
        json.dumps([{"customer_id": "cust-1"}]),
        encoding="utf-8",
    )
    (plaid_dir / "accounts_20260816T054139Z.json").write_text(
        json.dumps(
            [
                {
                    "account_id": "acct-1",
                    "customer_id": "cust-1",
                    "currency_code": "USD",
                    "current_balance": "200.00",
                    "opened_at": "2026-08-01T00:00:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )
    (plaid_dir / "transactions_20260816T054139Z.json").write_text(
        json.dumps(
            [
                {
                    "transaction_id": "txn-1",
                    "account_id": "acct-1",
                    "customer_id": "cust-1",
                    "transaction_type": "DEBIT",
                    "transaction_amount": "20.00",
                    "currency_code": "USD",
                    "transaction_status": "POSTED",
                    "event_timestamp": "2026-08-10T12:00:00Z",
                    "processing_timestamp": "2026-08-16T05:41:39.966868Z",
                    "merchant_category": "FOOD_AND_DRINK",
                    "country_code": "US",
                    "risk_score": 20,
                }
            ]
        ),
        encoding="utf-8",
    )

    staged = stage_plaid_batch_for_processing(
        canonical_root=canonical_root,
        bronze_root=bronze_root,
    )

    assert [item.dataset_name for item in staged] == [
        "customers",
        "accounts",
        "transactions",
        "securities",
        "daily_account_balances",
        "payments",
        "trades",
    ]
    assert (bronze_root / "customers" / "customers_20260816T054139Z.json").exists()
    assert (bronze_root / "accounts" / "accounts_20260816T054139Z.json").exists()
    assert (bronze_root / "transactions" / "transactions_20260816T054139Z.json").exists()
    assert json.loads(
        (bronze_root / "payments" / "payments_20260816T054139Z.json").read_text(encoding="utf-8")
    ) == []
    assert json.loads(
        (bronze_root / "trades" / "trades_20260816T054139Z.json").read_text(encoding="utf-8")
    ) == []
    daily_balances = json.loads(
        (
            bronze_root
            / "daily_account_balances"
            / "daily_account_balances_20260816T054139Z.json"
        ).read_text(encoding="utf-8")
    )
    assert len(daily_balances) == 1
