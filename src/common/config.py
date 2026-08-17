from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AccountsPerCustomerConfig(BaseModel):
    min: int = Field(ge=1)
    max: int = Field(ge=1)


class OutputFormatsConfig(BaseModel):
    batch: list[str]
    streaming: list[str]


class GenerationConfig(BaseModel):
    seed: int
    customers: int = Field(ge=1)
    accounts_per_customer: AccountsPerCustomerConfig
    transactions: int = Field(ge=1)
    payments: int = Field(ge=1)
    trades: int = Field(ge=1)
    securities: int = Field(ge=1)
    daily_balances_days: int = Field(ge=1)
    stream_events: int = Field(ge=1)
    late_event_ratio: float = Field(ge=0.0, le=1.0)
    duplicate_ratio: float = Field(ge=0.0, le=1.0)
    invalid_ratio: float = Field(ge=0.0, le=1.0)
    malformed_count: int = Field(ge=0)
    base_currency: str
    output_formats: OutputFormatsConfig


class PathsConfig(BaseModel):
    batch_dir: str
    streaming_dir: str


class AppConfig(BaseModel):
    env: str
    log_level: str


class Settings(BaseModel):
    app: AppConfig
    generation: GenerationConfig
    paths: PathsConfig


def load_settings(config_path: str | Path) -> Settings:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as handle:
      raw = yaml.safe_load(handle)
    return Settings.model_validate(raw)

