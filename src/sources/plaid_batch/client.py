from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any

import requests

from src.sources.plaid_batch.models import (
    PlaidConfig,
    PlaidInstitutionSearchResult,
    PlaidSandboxTransaction,
)


class PlaidBatchClient:
    def __init__(self, config: PlaidConfig) -> None:
        self.config = config

    def create_sandbox_public_token(
        self,
        *,
        override_username: str | None = None,
        override_password: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "institution_id": self.config.institution_id,
            "initial_products": ["transactions"],
        }
        if override_username or override_password:
            payload["options"] = {
                "override_username": override_username or "user_good",
                "override_password": override_password or "pass_good",
            }
        return self._post("/sandbox/public_token/create", payload)

    def create_link_token(
        self,
        *,
        user_id: str,
        full_name: str,
        email: str,
        country_codes: list[str] | None = None,
        products: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "client_name": self.config.client_name,
            "country_codes": country_codes or ["US"],
            "language": "en",
            "products": products or ["transactions"],
            "user": {
                "client_user_id": user_id,
                "legal_name": full_name,
                "email_address": email,
            },
        }
        if self.config.redirect_uri:
            payload["redirect_uri"] = self.config.redirect_uri
        if self.config.webhook_url:
            payload["webhook"] = self.config.webhook_url
        return self._post("/link/token/create", payload)

    def get_link_token(self, link_token: str) -> dict[str, Any]:
        return self._post(
            "/link/token/get",
            {
                "client_id": self.config.client_id,
                "secret": self.config.secret,
                "link_token": link_token,
            },
        )

    def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "public_token": public_token,
        }
        return self._post("/item/public_token/exchange", payload)

    def search_institutions(
        self,
        query: str,
        *,
        country_codes: list[str] | None = None,
        limit: int = 10,
    ) -> list[PlaidInstitutionSearchResult]:
        response = self._post(
            "/institutions/search",
            {
                "client_id": self.config.client_id,
                "secret": self.config.secret,
                "query": query,
                "country_codes": country_codes or ["US"],
                "products": ["transactions"],
                "options": {"include_optional_metadata": True},
            },
        )
        institutions = response.get("institutions", [])
        results = [
            PlaidInstitutionSearchResult(
                institution_id=str(record["institution_id"]),
                name=str(record["name"]),
            )
            for record in institutions[:limit]
            if isinstance(record, dict)
        ]
        return results

    def get_accounts(self, access_token: str) -> dict[str, Any]:
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "access_token": access_token,
        }
        return self._post("/accounts/get", payload)

    def get_institution(self) -> dict[str, Any]:
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "institution_id": self.config.institution_id,
            "country_codes": ["US"],
        }
        return self._post("/institutions/get_by_id", payload)

    def transactions_sync(self, access_token: str, cursor: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "access_token": access_token,
            "count": 500,
            "options": {"days_requested": self.config.days_requested},
        }
        if cursor is not None:
            payload["cursor"] = cursor
        return self._post("/transactions/sync", payload)

    def fetch_full_transactions_sync(self, access_token: str) -> list[dict[str, Any]]:
        cursor: str | None = None
        responses: list[dict[str, Any]] = []
        while True:
            response = self.transactions_sync(access_token, cursor=cursor)
            responses.append(response)
            if not response.get("has_more", False):
                return responses
            cursor = response.get("next_cursor")

    def create_sandbox_transactions(
        self,
        access_token: str,
        transactions: list[PlaidSandboxTransaction],
    ) -> dict[str, Any]:
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "access_token": access_token,
            "transactions": [transaction.model_dump() for transaction in transactions],
        }
        return self._post("/sandbox/transactions/create", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.config.base_url}{path}",
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("Plaid response payload must be a JSON object")
        return body


def default_sandbox_transactions(seed: str | None = None) -> list[PlaidSandboxTransaction]:
    today = datetime.now(UTC).date()
    random = Random(seed or today.isoformat())
    templates = [
        ("NAVY FEDERAL PAYROLL", (2200, 3200), 1),
        ("AUTO LOAN PAYMENT", (1800, 2900), 1),
        ("MEMBER TRANSFER CREDIT", (450, 900), 3),
        ("TRAVEL AIRLINE TICKET", (320, 760), 3),
        ("REFUND NAVY EXCHANGE", (60, 180), 5),
        ("UTILITY ELECTRIC BILL", (90, 220), 5),
        ("CASHBACK REWARD CREDIT", (45, 130), 7),
        ("COMMISSARY GROCERY", (80, 210), 7),
        ("INSURANCE REIMBURSEMENT CREDIT", (140, 320), 10),
        ("HEALTHCARE CLINIC COPAY", (100, 280), 10),
    ]
    transactions: list[PlaidSandboxTransaction] = []
    for description, amount_range, day_offset in templates:
        amount = round(random.uniform(*amount_range), 2)
        transactions.append(
            PlaidSandboxTransaction(
                amount=amount,
                description=description,
                date_transacted=(today - timedelta(days=day_offset)).isoformat(),
                date_posted=(today - timedelta(days=max(day_offset - 1, 0))).isoformat(),
            )
        )
    return transactions
