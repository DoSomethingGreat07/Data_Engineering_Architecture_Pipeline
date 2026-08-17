from __future__ import annotations

import yaml
from pydantic import BaseModel, Field


class CanonicalFieldContract(BaseModel):
    type: str
    required: bool
    derivation_allowed: bool


class CanonicalEntityContract(BaseModel):
    description: str | None = None
    required_fields: list[str]
    fields: dict[str, CanonicalFieldContract]


class MetadataRequirements(BaseModel):
    required_fields: list[str]


class CanonicalSchemaContract(BaseModel):
    version: int
    canonical_entities: dict[str, CanonicalEntityContract]
    metadata_requirements: MetadataRequirements


class FieldMapping(BaseModel):
    source_field: str
    target_field: str
    transform: str
    required: bool


class EntityMapping(BaseModel):
    canonical_entity: str
    source_object: str
    target_mode: str
    fields: list[FieldMapping]


class ProviderMetadata(BaseModel):
    source_system: str
    schema_version: int
    mapping_version: int


class ProviderMappingSpec(BaseModel):
    provider_name: str
    version: int
    source_modes: list[str]
    notes: list[str] = Field(default_factory=list)
    mappings: list[EntityMapping]
    metadata: ProviderMetadata


def load_canonical_schema_contract(path: str) -> CanonicalSchemaContract:
    with open(path, encoding="utf-8") as handle:
        return CanonicalSchemaContract.model_validate(yaml.safe_load(handle))


def load_provider_mapping_spec(path: str) -> ProviderMappingSpec:
    with open(path, encoding="utf-8") as handle:
        return ProviderMappingSpec.model_validate(yaml.safe_load(handle))
