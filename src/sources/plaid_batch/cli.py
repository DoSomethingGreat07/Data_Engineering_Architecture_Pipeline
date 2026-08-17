from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import Random

from src.common.env_utils import apply_env_overrides
from src.common.logging_utils import configure_logging
from src.sources.plaid_batch.client import PlaidBatchClient, default_sandbox_transactions
from src.sources.plaid_batch.models import CustomerContext, SandboxCustomerProfile
from src.sources.plaid_batch.service import (
    PlaidBatchExtractionService,
    build_plaid_config_from_env,
)

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract Plaid batch data and normalize it.")
    parser.add_argument("--output-dir", default="data/external_sources")
    parser.add_argument("--customer-id", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--country-code", default="US")
    parser.add_argument("--risk-score", type=int, default=25)
    parser.add_argument("--customer-count", type=int, default=20)
    parser.add_argument("--access-token", default=None)
    parser.add_argument("--create-sandbox-token-only", action="store_true")
    parser.add_argument("--seed-sandbox-transactions", action="store_true")
    parser.add_argument("--run-sandbox-seeded-extract", action="store_true")
    parser.add_argument("--scenario-seed", default=None)
    parser.add_argument("--print-record-limit", type=int, default=3)
    parser.add_argument("--create-link-token-only", action="store_true")
    parser.add_argument("--exchange-public-token", default=None)
    parser.add_argument("--search-institution", default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_sandbox_customer_profiles(
    *,
    customer_id: str,
    full_name: str,
    email: str,
    country_code: str,
    risk_score: int,
    customer_count: int,
    scenario_seed: str | None,
) -> list[SandboxCustomerProfile]:
    if customer_count <= 1:
        return [
            SandboxCustomerProfile(
                customer_context=CustomerContext(
                    customer_id=customer_id,
                    full_name=full_name,
                    email=email,
                    country_code=country_code,
                    risk_score=risk_score,
                ),
                seed=scenario_seed or customer_id,
            )
        ]
    random = Random(scenario_seed or customer_id)
    first_names = [
        "Alex", "Taylor", "Jordan", "Morgan", "Riley", "Avery", "Casey", "Drew",
        "Cameron", "Parker", "Quinn", "Reese", "Skyler", "Dakota", "Emerson",
        "Hayden", "Finley", "Harper", "Rowan", "Sage",
    ]
    last_names = [
        "Adams", "Bennett", "Carter", "Diaz", "Edwards", "Fisher", "Garcia",
        "Howard", "Irwin", "Johnson", "Kelly", "Lopez", "Morris", "Nguyen",
        "Owens", "Patel", "Reed", "Stewart", "Turner", "Walker",
    ]
    country_codes = ["US", "US", "US", "CA", "GB", "DE", "AU", "JP"]
    profiles: list[SandboxCustomerProfile] = []
    base_local, _, base_domain = email.partition("@")
    email_domain = base_domain or "example.com"
    for index in range(customer_count):
        first = first_names[index % len(first_names)]
        last = last_names[(index * 3) % len(last_names)]
        profile_country = country_codes[index % len(country_codes)]
        profile_risk = min(95, max(10, risk_score + random.randint(-12, 28)))
        created_at = datetime.now(UTC) - timedelta(days=random.randint(20, 540))
        context = CustomerContext(
            customer_id=f"{customer_id}-{index + 1:03d}",
            full_name=f"{first} {last}",
            email=f"{base_local}+{index + 1:03d}@{email_domain}",
            country_code=profile_country if profile_country else country_code,
            risk_score=profile_risk,
            created_at=created_at,
        )
        profiles.append(
            SandboxCustomerProfile(
                customer_context=context,
                seed=f"{scenario_seed or customer_id}-customer-{index + 1:03d}",
            )
        )
    return profiles


def main() -> int:
    args = build_parser().parse_args()
    apply_env_overrides()
    configure_logging(args.log_level)
    config = build_plaid_config_from_env()
    client = PlaidBatchClient(config)

    if args.search_institution:
        institutions = client.search_institutions(args.search_institution)
        print(json.dumps([item.model_dump() for item in institutions], indent=2))
        return 0

    if args.create_sandbox_token_only:
        public_token_response = client.create_sandbox_public_token(
            override_username="user_transactions_dynamic",
        )
        exchange_response = client.exchange_public_token(public_token_response["public_token"])
        if args.seed_sandbox_transactions:
            client.create_sandbox_transactions(
                exchange_response["access_token"],
                default_sandbox_transactions(seed=args.scenario_seed),
            )
        LOGGER.info(
            "created sandbox access token",
            extra={"item_id": exchange_response.get("item_id"), "access_token": "[redacted]"},
        )
        return 0

    if args.run_sandbox_seeded_extract:
        service = PlaidBatchExtractionService(client)
        profiles = build_sandbox_customer_profiles(
            customer_id=args.customer_id,
            full_name=args.full_name,
            email=args.email,
            country_code=args.country_code,
            risk_score=args.risk_score,
            customer_count=args.customer_count,
            scenario_seed=args.scenario_seed,
        )
        raw_bundles = []
        normalized_bundles = []
        item_ids: list[str] = []
        for profile in profiles:
            public_token_response = client.create_sandbox_public_token(
                override_username="user_transactions_dynamic",
            )
            exchange_response = client.exchange_public_token(public_token_response["public_token"])
            item_ids.append(str(exchange_response.get("item_id", "")))
            client.create_sandbox_transactions(
                exchange_response["access_token"],
                default_sandbox_transactions(seed=profile.seed),
            )
            raw_bundle = service.fetch_raw_bundle(exchange_response["access_token"])
            normalized_bundle = service.normalize(raw_bundle, profile.customer_context)
            raw_bundles.append(raw_bundle)
            normalized_bundles.append(normalized_bundle)
        raw_bundle = service.combine_raw_bundles(raw_bundles)
        normalized_bundle = service.combine_normalized_bundles(normalized_bundles)
        paths = service.write_bundle(
            output_dir=Path(args.output_dir),
            raw_bundle=raw_bundle,
            normalized_bundle=normalized_bundle,
        )
        print(
            json.dumps(
                {
                    "institution": normalized_bundle.metadata.get("institution"),
                    "item_id_count": len([item for item in item_ids if item]),
                    "customer_count": len(normalized_bundle.customers),
                    "accounts_count": len(normalized_bundle.accounts),
                    "transactions_count": len(normalized_bundle.transactions),
                    "accounts_sample": normalized_bundle.accounts[: args.print_record_limit],
                    "transactions_sample": normalized_bundle.transactions[
                        : args.print_record_limit
                    ],
                    "output_files": {
                        "raw_accounts_path": str(paths.raw_accounts_path),
                        "raw_transactions_path": str(paths.raw_transactions_path),
                        "canonical_accounts_path": str(paths.canonical_accounts_path),
                        "canonical_transactions_path": str(paths.canonical_transactions_path),
                    },
                },
                indent=2,
            )
        )
        return 0

    if args.create_link_token_only:
        link_response = client.create_link_token(
            user_id=args.customer_id,
            full_name=args.full_name,
            email=args.email,
            country_codes=[args.country_code],
            products=["transactions"],
        )
        print(
            json.dumps(
                {
                    "link_token": link_response.get("link_token"),
                    "expiration": link_response.get("expiration"),
                    "request_id": link_response.get("request_id"),
                },
                indent=2,
            )
        )
        return 0

    if args.exchange_public_token:
        exchange_response = client.exchange_public_token(args.exchange_public_token)
        print(
            json.dumps(
                {
                    "item_id": exchange_response.get("item_id"),
                    "access_token": exchange_response.get("access_token"),
                },
                indent=2,
            )
        )
        return 0

    access_token = args.access_token or config.access_token
    if not access_token:
        raise ValueError("Plaid access token is required via --access-token or PLAID_ACCESS_TOKEN")

    context = CustomerContext(
        customer_id=args.customer_id,
        full_name=args.full_name,
        email=args.email,
        country_code=args.country_code,
        risk_score=args.risk_score,
    )
    service = PlaidBatchExtractionService(client)
    raw_bundle = service.fetch_raw_bundle(access_token)
    normalized_bundle = service.normalize(raw_bundle, context)
    paths = service.write_bundle(
        output_dir=Path(args.output_dir),
        raw_bundle=raw_bundle,
        normalized_bundle=normalized_bundle,
    )
    LOGGER.info(
        "plaid batch extraction complete",
        extra={
            "raw_accounts_path": str(paths.raw_accounts_path),
            "raw_transactions_path": str(paths.raw_transactions_path),
            "canonical_accounts_path": str(paths.canonical_accounts_path),
            "canonical_transactions_path": str(paths.canonical_transactions_path),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
