from __future__ import annotations


def source_format_for_dataset(dataset_name: str) -> str:
    source_format_by_dataset = {
        "customers": "json",
        "accounts": "json",
        "securities": "json",
        "transactions": "json",
        "payments": "json",
        "trades": "json",
        "daily_account_balances": "json",
    }
    return source_format_by_dataset[dataset_name]
