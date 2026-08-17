from __future__ import annotations

from dataclasses import dataclass

from src.common.schema_contracts import CanonicalSchemaContract, ProviderMappingSpec


@dataclass(frozen=True)
class MappingValidationIssue:
    provider_name: str
    canonical_entity: str
    field_name: str
    issue: str


def validate_provider_mapping(
    contract: CanonicalSchemaContract, mapping: ProviderMappingSpec
) -> list[MappingValidationIssue]:
    issues: list[MappingValidationIssue] = []

    for entity_mapping in mapping.mappings:
        if entity_mapping.canonical_entity not in contract.canonical_entities:
            issues.append(
                MappingValidationIssue(
                    provider_name=mapping.provider_name,
                    canonical_entity=entity_mapping.canonical_entity,
                    field_name="*",
                    issue="unknown canonical entity",
                )
            )
            continue

        entity_contract = contract.canonical_entities[entity_mapping.canonical_entity]
        mapped_fields = {field.target_field for field in entity_mapping.fields}

        for required_field in entity_contract.required_fields:
            if required_field not in mapped_fields:
                field_contract = entity_contract.fields[required_field]
                if not field_contract.derivation_allowed:
                    issues.append(
                        MappingValidationIssue(
                            provider_name=mapping.provider_name,
                            canonical_entity=entity_mapping.canonical_entity,
                            field_name=required_field,
                            issue="required field missing and derivation not allowed",
                        )
                    )

        for field_mapping in entity_mapping.fields:
            if field_mapping.target_field not in entity_contract.fields:
                issues.append(
                    MappingValidationIssue(
                        provider_name=mapping.provider_name,
                        canonical_entity=entity_mapping.canonical_entity,
                        field_name=field_mapping.target_field,
                        issue="mapped target field not in canonical contract",
                    )
                )

    return issues

