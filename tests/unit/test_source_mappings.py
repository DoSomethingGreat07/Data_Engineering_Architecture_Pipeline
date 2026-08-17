from src.common.schema_contracts import (
    load_canonical_schema_contract,
    load_provider_mapping_spec,
)
from src.common.source_mapping_validation import validate_provider_mapping


def test_canonical_schema_contract_loads() -> None:
    contract = load_canonical_schema_contract(
        "config/source_mappings/canonical_schema_contract.yaml"
    )
    assert contract.version == 1
    assert "transactions" in contract.canonical_entities


def test_plaid_mapping_passes_contract_validation() -> None:
    contract = load_canonical_schema_contract(
        "config/source_mappings/canonical_schema_contract.yaml"
    )
    mapping = load_provider_mapping_spec("config/source_mappings/providers/plaid_sandbox.yaml")
    issues = validate_provider_mapping(contract, mapping)
    assert issues == []


def test_alpaca_mapping_passes_contract_validation() -> None:
    contract = load_canonical_schema_contract(
        "config/source_mappings/canonical_schema_contract.yaml"
    )
    mapping = load_provider_mapping_spec(
        "config/source_mappings/providers/alpaca_market_data.yaml"
    )
    issues = validate_provider_mapping(contract, mapping)
    assert issues == []


def test_alpha_vantage_mapping_passes_contract_validation() -> None:
    contract = load_canonical_schema_contract(
        "config/source_mappings/canonical_schema_contract.yaml"
    )
    mapping = load_provider_mapping_spec(
        "config/source_mappings/providers/alpha_vantage_reference.yaml"
    )
    issues = validate_provider_mapping(contract, mapping)
    assert issues == []


def test_sec_mapping_passes_contract_validation() -> None:
    contract = load_canonical_schema_contract(
        "config/source_mappings/canonical_schema_contract.yaml"
    )
    mapping = load_provider_mapping_spec("config/source_mappings/providers/sec_edgar_bulk.yaml")
    issues = validate_provider_mapping(contract, mapping)
    assert issues == []
