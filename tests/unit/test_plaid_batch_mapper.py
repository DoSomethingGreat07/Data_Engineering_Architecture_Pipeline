from datetime import UTC, datetime
from pathlib import Path

from src.sources.plaid_batch.mapper import (
    classify_merchant_category,
    derive_risk_score,
    map_plaid_bundle,
    map_plaid_transaction_type,
)
from src.sources.plaid_batch.models import CustomerContext, PlaidRawBundle
from src.sources.plaid_batch.service import PlaidBatchExtractionService


def build_context() -> CustomerContext:
    return CustomerContext(
        customer_id="CUST-NFCU-001",
        full_name="Navy Federal Member",
        email="member@example.com",
        country_code="US",
        risk_score=30,
        created_at=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
    )


def build_raw_bundle() -> PlaidRawBundle:
    return PlaidRawBundle(
        institution={"institution": {"name": "Navy Federal Credit Union"}},
        accounts_response={
            "accounts": [
                {
                    "account_id": "acct_1",
                    "type": "depository",
                    "subtype": "checking",
                    "balances": {"current": 1250.55, "iso_currency_code": "USD"},
                }
            ]
        },
        transactions_sync_responses=[
            {
                "added": [
                    {
                        "transaction_id": "txn_1",
                        "account_id": "acct_1",
                        "amount": 42.25,
                        "pending": False,
                        "authorized_datetime": "2026-08-14T14:15:00Z",
                        "merchant_name": "Coffee Shop",
                        "iso_currency_code": "USD",
                        "location": {"country": "US"},
                        "personal_finance_category": {"primary": "FOOD_AND_DRINK"},
                    }
                ],
                "has_more": False,
            }
        ],
    )


def test_map_plaid_bundle_creates_canonical_records() -> None:
    bundle = map_plaid_bundle(build_raw_bundle(), build_context())
    assert bundle.customers[0]["customer_id"] == "CUST-NFCU-001"
    assert bundle.accounts[0]["account_id"] == "acct_1"
    assert bundle.transactions[0]["transaction_id"] == "txn_1"
    assert bundle.metadata["source_system"] == "plaid"


def test_transaction_type_mapping_prefers_credit_for_payroll() -> None:
    assert (
        map_plaid_transaction_type(
            {"personal_finance_category": {"primary": "PAYROLL"}, "amount": 100.0}
        )
        == "CREDIT"
    )


def test_derive_risk_score_increases_for_large_amounts() -> None:
    low = derive_risk_score({"amount": 20, "pending": False, "location": {"country": "US"}})
    high = derive_risk_score(
        {"amount": 6000, "pending": True, "location": {"country": "GB"}}
    )
    assert high > low


def test_classify_merchant_category_uses_description_keywords() -> None:
    category = classify_merchant_category({"name": "Utility Electric Bill"})
    assert category == "UTILITIES"


def test_write_bundle_creates_output_files(tmp_path: Path) -> None:
    service = PlaidBatchExtractionService(client=None)  # type: ignore[arg-type]
    paths = service.write_bundle(
        output_dir=tmp_path,
        raw_bundle=build_raw_bundle(),
        normalized_bundle=map_plaid_bundle(build_raw_bundle(), build_context()),
    )
    assert paths.raw_accounts_path.exists()
    assert paths.canonical_transactions_path.exists()
