from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.common.constants import (
    COUNTRY_CODES,
    INVALID_CURRENCY_CODE,
    VALID_CURRENCY_CODES,
    VALID_PAYMENT_STATUSES,
    VALID_TRADE_SIDES,
    VALID_TRANSACTION_STATUSES,
    VALID_TRANSACTION_TYPES,
)


class CustomerRecord(BaseModel):
    customer_id: str
    full_name: str
    email: str
    country_code: str
    risk_score: int = Field(ge=0, le=100)
    created_at: datetime

    @field_validator("country_code")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if value not in COUNTRY_CODES:
            raise ValueError("unsupported country code")
        return value


class AccountRecord(BaseModel):
    account_id: str
    customer_id: str
    account_type: Literal["CHECKING", "SAVINGS", "BROKERAGE"]
    currency_code: str
    current_balance: Decimal
    opened_at: datetime
    status: Literal["OPEN", "SUSPENDED", "CLOSED"]

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value not in VALID_CURRENCY_CODES:
            raise ValueError("unsupported currency code")
        return value


class SecurityRecord(BaseModel):
    security_id: str
    ticker: str
    security_name: str
    security_type: str
    exchange_code: str
    currency_code: str

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value not in VALID_CURRENCY_CODES:
            raise ValueError("unsupported currency code")
        return value


class TransactionRecord(BaseModel):
    transaction_id: str
    account_id: str
    customer_id: str
    transaction_type: str
    transaction_amount: Decimal
    currency_code: str
    transaction_status: str
    event_timestamp: datetime
    processing_timestamp: datetime
    merchant_category: str
    country_code: str
    risk_score: int = Field(ge=0, le=100)

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in VALID_TRANSACTION_TYPES:
            raise ValueError("invalid transaction type")
        return value

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value == INVALID_CURRENCY_CODE or value not in VALID_CURRENCY_CODES:
            raise ValueError("unsupported currency code")
        return value

    @field_validator("transaction_status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_TRANSACTION_STATUSES:
            raise ValueError("invalid transaction status")
        return value


class PaymentRecord(BaseModel):
    payment_id: str
    account_id: str
    customer_id: str
    transaction_amount: Decimal
    currency_code: str
    transaction_status: str
    event_timestamp: datetime
    processing_timestamp: datetime
    counterparty_account_id: str
    country_code: str
    risk_score: int = Field(ge=0, le=100)

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value == INVALID_CURRENCY_CODE or value not in VALID_CURRENCY_CODES:
            raise ValueError("unsupported currency code")
        return value

    @field_validator("transaction_status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_PAYMENT_STATUSES:
            raise ValueError("invalid payment status")
        return value


class TradeRecord(BaseModel):
    trade_id: str
    account_id: str
    customer_id: str
    security_id: str
    quantity: Decimal
    price: Decimal
    transaction_amount: Decimal
    currency_code: str
    side: str
    transaction_status: str
    event_timestamp: datetime
    processing_timestamp: datetime
    country_code: str
    risk_score: int = Field(ge=0, le=100)

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value == INVALID_CURRENCY_CODE or value not in VALID_CURRENCY_CODES:
            raise ValueError("unsupported currency code")
        return value

    @field_validator("side")
    @classmethod
    def validate_side(cls, value: str) -> str:
        if value not in VALID_TRADE_SIDES:
            raise ValueError("invalid trade side")
        return value

    @field_validator("transaction_status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_TRANSACTION_STATUSES:
            raise ValueError("invalid trade status")
        return value


class DailyBalanceRecord(BaseModel):
    balance_id: str
    account_id: str
    customer_id: str
    balance_date: datetime
    opening_balance: Decimal
    closing_balance: Decimal
    currency_code: str

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value not in VALID_CURRENCY_CODES:
            raise ValueError("unsupported currency code")
        return value

