from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.common.schemas import TransactionRecord


def test_transaction_schema_accepts_valid_record() -> None:
    record = TransactionRecord(
        transaction_id="TXN-1",
        account_id="ACCT-1",
        customer_id="CUST-1",
        transaction_type="DEBIT",
        transaction_amount=Decimal("10.50"),
        currency_code="USD",
        transaction_status="POSTED",
        event_timestamp=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        processing_timestamp=datetime(2026, 8, 15, 12, 5, tzinfo=UTC),
        merchant_category="GROCERY",
        country_code="US",
        risk_score=10,
    )
    assert record.transaction_id == "TXN-1"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("currency_code", "ZZZ"),
        ("transaction_type", "INVALID"),
        ("transaction_status", "UNKNOWN"),
    ],
)
def test_transaction_schema_rejects_invalid_values(field: str, value: str) -> None:
    payload = {
        "transaction_id": "TXN-1",
        "account_id": "ACCT-1",
        "customer_id": "CUST-1",
        "transaction_type": "DEBIT",
        "transaction_amount": Decimal("10.50"),
        "currency_code": "USD",
        "transaction_status": "POSTED",
        "event_timestamp": datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        "processing_timestamp": datetime(2026, 8, 15, 12, 5, tzinfo=UTC),
        "merchant_category": "GROCERY",
        "country_code": "US",
        "risk_score": 10,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        TransactionRecord(**payload)

