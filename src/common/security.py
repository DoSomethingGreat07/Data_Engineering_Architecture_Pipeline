from __future__ import annotations

import hashlib
from dataclasses import dataclass


def deterministic_hash(value: str, salt: str = "financial-data-platform") -> str:
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{masked_local}@{domain}"


def canonical_security_id_from_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol must not be empty")
    return f"SEC-{normalized}"


@dataclass(frozen=True)
class SensitiveFieldPolicy:
    field_name: str
    classification: str
    treatment: str


SENSITIVE_FIELD_POLICIES = [
    SensitiveFieldPolicy("full_name", "PII", "hash_or_mask_in_logs"),
    SensitiveFieldPolicy("email", "PII", "mask_in_logs_hash_for_exports"),
    SensitiveFieldPolicy("customer_id", "Confidential", "hash_when_shared_outside_platform"),
    SensitiveFieldPolicy("account_id", "Confidential", "hash_when_shared_outside_platform"),
]
