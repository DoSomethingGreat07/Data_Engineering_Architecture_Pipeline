# Source Mapping Framework

This directory defines how external batch files and APIs map into the canonical platform schema.

Core rule:
- External source payloads do **not** redefine the platform schema.
- Every source must map into the canonical entities already implemented in the repo.

Mapping file structure:
- `canonical_schema_contract.yaml`
  The canonical field contract for each entity.
- `providers/*.yaml`
  Source-specific mappings into the canonical contract.

Each provider mapping must specify:
- source system name
- source mode (`batch`, `streaming`, `reference`)
- canonical entity
- source field
- target field
- transform rule
- required flag
- fallback or derivation rule when needed
- metadata behavior

Validation rules:
- Every required canonical field must be mapped, derived, or explicitly marked unavailable.
- Unsupported or missing required fields must be surfaced before implementation proceeds.
- Raw source payloads should still be retained for lineage and debugging.

