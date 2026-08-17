from src.common.security import (
    canonical_security_id_from_symbol,
    deterministic_hash,
    mask_email,
)


def test_deterministic_hash_is_stable() -> None:
    assert deterministic_hash("value") == deterministic_hash("value")


def test_mask_email_preserves_domain() -> None:
    assert mask_email("user@example.com").endswith("@example.com")
    assert "*" in mask_email("user@example.com")


def test_canonical_security_id_from_symbol_is_normalized() -> None:
    assert canonical_security_id_from_symbol(" aapl ") == "SEC-AAPL"
