from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast

from src.common.schemas import AccountRecord, CustomerRecord, TransactionRecord
from src.sources.plaid_batch.models import (
    CustomerContext,
    PlaidNormalizedBundle,
    PlaidRawBundle,
)

ACCOUNT_TYPE_MAP = {
    "depository": "CHECKING",
    "credit": "CHECKING",
    "loan": "CHECKING",
    "investment": "BROKERAGE",
    "brokerage": "BROKERAGE",
}


def map_plaid_bundle(
    raw_bundle: PlaidRawBundle,
    customer_context: CustomerContext,
) -> PlaidNormalizedBundle:
    customers = [map_customer(customer_context)]
    accounts = [
        map_account(record, customer_context.customer_id)
        for record in raw_bundle.accounts_response.get("accounts", [])
    ]
    account_customer_map = {
        account["account_id"]: customer_context.customer_id for account in accounts
    }
    extraction_time = datetime.now(UTC)
    transactions = []
    for response in raw_bundle.transactions_sync_responses:
        for record in response.get("added", []):
            transactions.append(
                map_transaction(
                    record,
                    account_customer_map=account_customer_map,
                    customer_context=customer_context,
                )
            )
    metadata = {
        "source_system": "plaid",
        "source_mode": "batch",
        "source_endpoint_or_file": "accounts/get + transactions/sync",
        "source_record_id": customer_context.customer_id,
        "ingestion_timestamp": extraction_time.isoformat(),
        "processing_timestamp": extraction_time.isoformat(),
        "ingestion_id": (
            f"plaid-{customer_context.customer_id}-"
            f"{extraction_time.strftime('%Y%m%dT%H%M%SZ')}"
        ),
        "raw_payload_checksum": compute_bundle_checksum(raw_bundle.model_dump(mode="json")),
        "raw_payload_location": "raw/plaid/",
        "schema_version": 1,
        "mapping_version": 1,
        "institution": (raw_bundle.institution or {}).get("institution", {}).get("name", "unknown"),
    }
    return PlaidNormalizedBundle(
        customers=customers,
        accounts=accounts,
        transactions=transactions,
        metadata=metadata,
    )


def map_customer(context: CustomerContext) -> dict[str, Any]:
    record = CustomerRecord(
        customer_id=context.customer_id,
        full_name=context.full_name,
        email=context.email,
        country_code=context.country_code,
        risk_score=context.risk_score,
        created_at=context.created_at,
    )
    return record.model_dump(mode="json")


def map_account(account: dict[str, Any], customer_id: str) -> dict[str, Any]:
    subtype = str(account.get("subtype", "")).lower()
    raw_type = str(account.get("type", "")).lower()
    derived_account_type = (
        "SAVINGS" if "savings" in subtype else ACCOUNT_TYPE_MAP.get(raw_type, "CHECKING")
    )
    account_type = cast(
        Literal["CHECKING", "SAVINGS", "BROKERAGE"],
        derived_account_type,
    )
    status: Literal["OPEN", "SUSPENDED", "CLOSED"] = "OPEN"
    opened_at = datetime.now(UTC)
    record = AccountRecord(
        account_id=account["account_id"],
        customer_id=customer_id,
        account_type=account_type,
        currency_code=account.get("balances", {}).get("iso_currency_code") or "USD",
        current_balance=Decimal(str(account.get("balances", {}).get("current", 0))),
        opened_at=opened_at,
        status=status,
    )
    return record.model_dump(mode="json")


def map_transaction(
    transaction: dict[str, Any],
    *,
    account_customer_map: dict[str, str],
    customer_context: CustomerContext,
) -> dict[str, Any]:
    event_timestamp = _coerce_datetime(
        transaction.get("authorized_datetime")
        or transaction.get("datetime")
        or transaction.get("date")
    )
    merchant_category = classify_merchant_category(transaction)
    status = "PENDING" if transaction.get("pending", False) else "POSTED"
    transaction_type = map_plaid_transaction_type(transaction)
    record = TransactionRecord(
        transaction_id=transaction["transaction_id"],
        account_id=transaction["account_id"],
        customer_id=account_customer_map.get(
            transaction["account_id"], customer_context.customer_id
        ),
        transaction_type=transaction_type,
        transaction_amount=Decimal(str(abs(transaction.get("amount", 0)))),
        currency_code=transaction.get("iso_currency_code") or "USD",
        transaction_status=status,
        event_timestamp=event_timestamp,
        processing_timestamp=datetime.now(UTC),
        merchant_category=merchant_category,
        country_code=(
            (transaction.get("location", {}) or {}).get("country")
            or customer_context.country_code
        ),
        risk_score=derive_risk_score(transaction),
    )
    return record.model_dump(mode="json")


def map_plaid_transaction_type(transaction: dict[str, Any]) -> str:
    category = (
        transaction.get("personal_finance_category", {}).get("primary", "").upper()
    )
    merchant_text = _transaction_text(transaction)
    if "PAYROLL" in category:
        return "CREDIT"
    if "TRANSFER" in category or "LOAN" in category:
        return "WIRE"
    if any(
        keyword in merchant_text
        for keyword in {"PAYROLL", "REFUND", "REVERSAL", "REWARD", "REIMBURSEMENT"}
    ):
        return "CREDIT"
    if any(keyword in merchant_text for keyword in {"TRANSFER", "WIRE", "ACH"}):
        return "WIRE"
    if any(keyword in merchant_text for keyword in {"FEE", "SERVICE CHARGE"}):
        return "FEE"
    if transaction.get("amount", 0) < 0:
        return "CREDIT"
    return "DEBIT"


def derive_risk_score(transaction: dict[str, Any]) -> int:
    amount = abs(float(transaction.get("amount", 0)))
    pending = bool(transaction.get("pending", False))
    score = 20
    if amount > 1000:
        score += 20
    if amount > 5000:
        score += 20
    if pending:
        score += 10
    if transaction.get("location", {}).get("country") not in {None, "US"}:
        score += 15
    return min(score, 100)


def classify_merchant_category(transaction: dict[str, Any]) -> str:
    category = transaction.get("personal_finance_category", {}).get("primary")
    if category:
        return str(category).upper()
    merchant_text = _transaction_text(transaction)
    keyword_map = {
        "PAYROLL": "PAYROLL",
        "GROCERY": "GROCERY",
        "COMMISSARY": "GROCERY",
        "FUEL": "TRAVEL",
        "AIRLINE": "TRAVEL",
        "TRAVEL": "TRAVEL",
        "UTILITY": "UTILITIES",
        "WATER": "UTILITIES",
        "ELECTRIC": "UTILITIES",
        "DINING": "DINING",
        "CAFE": "DINING",
        "HEALTH": "HEALTHCARE",
        "CLINIC": "HEALTHCARE",
        "BROKERAGE": "BROKERAGE",
        "TRANSFER": "BROKERAGE",
    }
    for keyword, normalized in keyword_map.items():
        if keyword in merchant_text:
            return normalized
    merchant_name = transaction.get("merchant_name") or transaction.get("name")
    if merchant_name:
        return str(merchant_name).upper()
    return "UNKNOWN"


def _coerce_datetime(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if "T" not in value:
        return datetime.fromisoformat(f"{value}T00:00:00+00:00")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compute_bundle_checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _transaction_text(transaction: dict[str, Any]) -> str:
    parts = [
        str(transaction.get("merchant_name") or ""),
        str(transaction.get("name") or ""),
        str(transaction.get("original_description") or ""),
        str(transaction.get("personal_finance_category", {}).get("primary") or ""),
    ]
    return " ".join(parts).upper()
