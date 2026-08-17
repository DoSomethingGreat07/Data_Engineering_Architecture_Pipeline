from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ExpectationSpec(BaseModel):
    expectation_type: str
    kwargs: dict[str, Any] = Field(default_factory=dict)


class SuiteSpec(BaseModel):
    suite_name: str
    expectations: list[ExpectationSpec]


class ValidationSummary(BaseModel):
    suite_name: str
    success: bool
    statistics: dict[str, Any]
    run_identifier: str
    stage: str
    dataset_name: str
    result_path: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        suite_name: str,
        success: bool,
        statistics: dict[str, Any],
        stage: str,
        dataset_name: str,
        result_path: str,
    ) -> ValidationSummary:
        timestamp = datetime.now(UTC)
        return cls(
            suite_name=suite_name,
            success=success,
            statistics=statistics,
            run_identifier=f"{suite_name}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}",
            stage=stage,
            dataset_name=dataset_name,
            result_path=result_path,
            created_at=timestamp,
        )


def suite_spec_path(ge_root: str | Path, suite_name: str) -> Path:
    return Path(ge_root) / "expectations" / f"{suite_name}.json"
