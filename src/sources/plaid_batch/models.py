from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class PlaidConfig(BaseModel):
    client_id: str
    secret: str
    env: str = "sandbox"
    access_token: str | None = None
    institution_id: str = "ins_56"
    days_requested: int = Field(default=30, ge=1, le=730)
    redirect_uri: str | None = None
    webhook_url: str | None = None
    client_name: str = "Production Pipeline"

    @property
    def base_url(self) -> str:
        environments = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }
        if self.env not in environments:
            raise ValueError(f"unsupported Plaid environment: {self.env}")
        return environments[self.env]


class CustomerContext(BaseModel):
    customer_id: str
    full_name: str
    email: str
    country_code: str = "US"
    risk_score: int = Field(default=25, ge=0, le=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlaidRawBundle(BaseModel):
    institution: dict[str, Any] | None = None
    accounts_response: dict[str, Any]
    transactions_sync_responses: list[dict[str, Any]]


class PlaidNormalizedBundle(BaseModel):
    customers: list[dict[str, Any]]
    accounts: list[dict[str, Any]]
    transactions: list[dict[str, Any]]
    metadata: dict[str, Any]


class PlaidOutputPaths(BaseModel):
    raw_accounts_path: Path
    raw_transactions_path: Path
    canonical_customers_path: Path
    canonical_accounts_path: Path
    canonical_transactions_path: Path
    metadata_path: Path


class PlaidInstitutionSearchResult(BaseModel):
    institution_id: str
    name: str


class PlaidSandboxTransaction(BaseModel):
    amount: float
    description: str
    date_transacted: str
    date_posted: str
    iso_currency_code: str = "USD"


class SandboxCustomerProfile(BaseModel):
    customer_context: CustomerContext
    seed: str
