from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.sources.plaid_batch.client import PlaidBatchClient
from src.sources.plaid_batch.mapper import map_plaid_bundle
from src.sources.plaid_batch.models import (
    CustomerContext,
    PlaidConfig,
    PlaidNormalizedBundle,
    PlaidOutputPaths,
    PlaidRawBundle,
)


class PlaidBatchExtractionService:
    def __init__(self, client: PlaidBatchClient) -> None:
        self.client = client

    def fetch_raw_bundle(self, access_token: str) -> PlaidRawBundle:
        institution = self.client.get_institution()
        accounts = self.client.get_accounts(access_token)
        transactions = self.client.fetch_full_transactions_sync(access_token)
        return PlaidRawBundle(
            institution=institution,
            accounts_response=accounts,
            transactions_sync_responses=transactions,
        )

    def normalize(
        self,
        raw_bundle: PlaidRawBundle,
        customer_context: CustomerContext,
    ) -> PlaidNormalizedBundle:
        return map_plaid_bundle(raw_bundle, customer_context)

    def write_bundle(
        self,
        *,
        output_dir: str | Path,
        raw_bundle: PlaidRawBundle,
        normalized_bundle: PlaidNormalizedBundle,
    ) -> PlaidOutputPaths:
        output_root = Path(output_dir)
        raw_dir = output_root / "raw" / "plaid"
        canonical_dir = output_root / "canonical" / "plaid"
        raw_dir.mkdir(parents=True, exist_ok=True)
        canonical_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        raw_accounts_path = raw_dir / f"accounts_{timestamp}.json"
        raw_transactions_path = raw_dir / f"transactions_sync_{timestamp}.json"
        canonical_customers_path = canonical_dir / f"customers_{timestamp}.json"
        canonical_accounts_path = canonical_dir / f"accounts_{timestamp}.json"
        canonical_transactions_path = canonical_dir / f"transactions_{timestamp}.json"
        metadata_path = canonical_dir / f"plaid_bundle_metadata_{timestamp}.json"

        raw_accounts_path.write_text(
            json.dumps(raw_bundle.accounts_response, indent=2),
            encoding="utf-8",
        )
        raw_transactions_path.write_text(
            json.dumps(raw_bundle.transactions_sync_responses, indent=2),
            encoding="utf-8",
        )
        canonical_customers_path.write_text(
            json.dumps(normalized_bundle.customers, indent=2),
            encoding="utf-8",
        )
        canonical_accounts_path.write_text(
            json.dumps(normalized_bundle.accounts, indent=2),
            encoding="utf-8",
        )
        canonical_transactions_path.write_text(
            json.dumps(normalized_bundle.transactions, indent=2),
            encoding="utf-8",
        )
        metadata_path.write_text(
            json.dumps(normalized_bundle.metadata, indent=2),
            encoding="utf-8",
        )

        return PlaidOutputPaths(
            raw_accounts_path=raw_accounts_path,
            raw_transactions_path=raw_transactions_path,
            canonical_customers_path=canonical_customers_path,
            canonical_accounts_path=canonical_accounts_path,
            canonical_transactions_path=canonical_transactions_path,
            metadata_path=metadata_path,
        )

    @staticmethod
    def combine_raw_bundles(raw_bundles: list[PlaidRawBundle]) -> PlaidRawBundle:
        accounts: list[dict[str, object]] = []
        transactions: list[dict[str, object]] = []
        institution = raw_bundles[0].institution if raw_bundles else None
        for bundle in raw_bundles:
            accounts.extend(bundle.accounts_response.get("accounts", []))
            transactions.extend(bundle.transactions_sync_responses)
        return PlaidRawBundle(
            institution=institution,
            accounts_response={"accounts": accounts},
            transactions_sync_responses=transactions,
        )

    @staticmethod
    def combine_normalized_bundles(
        bundles: list[PlaidNormalizedBundle],
    ) -> PlaidNormalizedBundle:
        customers: list[dict[str, object]] = []
        accounts: list[dict[str, object]] = []
        transactions: list[dict[str, object]] = []
        institution = "unknown"
        processing_timestamp = datetime.now(UTC).isoformat()
        for bundle in bundles:
            customers.extend(bundle.customers)
            accounts.extend(bundle.accounts)
            transactions.extend(bundle.transactions)
            institution = str(bundle.metadata.get("institution", institution))
        metadata = {
            "source_system": "plaid",
            "source_mode": "batch",
            "source_endpoint_or_file": "accounts/get + transactions/sync",
            "source_record_id": "MULTI-CUSTOMER",
            "ingestion_timestamp": processing_timestamp,
            "processing_timestamp": processing_timestamp,
            "ingestion_id": f"plaid-multi-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
            "raw_payload_location": "raw/plaid/",
            "schema_version": 1,
            "mapping_version": 2,
            "institution": institution,
            "customer_count": len(customers),
            "account_count": len(accounts),
            "transaction_count": len(transactions),
        }
        return PlaidNormalizedBundle(
            customers=customers,
            accounts=accounts,
            transactions=transactions,
            metadata=metadata,
        )


def build_plaid_config_from_env() -> PlaidConfig:
    import os

    return PlaidConfig(
        client_id=os.environ.get("PLAID_CLIENT_ID", ""),
        secret=os.environ.get("PLAID_SECRET", ""),
        env=os.environ.get("PLAID_ENV", "sandbox"),
        access_token=os.environ.get("PLAID_ACCESS_TOKEN") or None,
        institution_id=os.environ.get("PLAID_INSTITUTION_ID", "ins_56"),
        days_requested=int(os.environ.get("PLAID_DAYS_REQUESTED", "30")),
        redirect_uri=os.environ.get("PLAID_REDIRECT_URI") or None,
        webhook_url=os.environ.get("PLAID_WEBHOOK_URL") or None,
        client_name=os.environ.get("PLAID_CLIENT_NAME", "Production Pipeline"),
    )
