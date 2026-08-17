from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.validation.models import ValidationSummary


def write_validation_summary(path: str | Path, summary: ValidationSummary) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return output_path


def build_cloudwatch_metric_payload(summary: ValidationSummary) -> dict[str, Any]:
    unsuccessful = 0 if summary.success else 1
    return {
        "Namespace": "FinancialDataPlatform",
        "MetricData": [
            {
                "MetricName": "GreatExpectationsFailures",
                "Dimensions": [
                    {"Name": "SuiteName", "Value": summary.suite_name},
                    {"Name": "DatasetName", "Value": summary.dataset_name},
                    {"Name": "Stage", "Value": summary.stage},
                ],
                "Value": unsuccessful,
                "Unit": "Count",
            }
        ],
    }


def write_metric_payload(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path

