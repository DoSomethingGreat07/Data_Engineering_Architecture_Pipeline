from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MetricDimension:
    name: str
    value: str


@dataclass(frozen=True)
class MetricDatum:
    metric_name: str
    value: float
    unit: str = "Count"
    dimensions: list[MetricDimension] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )


def build_metric_payload(namespace: str, metric_data: list[MetricDatum]) -> dict[str, Any]:
    return {
        "Namespace": namespace,
        "MetricData": [
            {
                "MetricName": datum.metric_name,
                "Value": datum.value,
                "Unit": datum.unit,
                "Timestamp": datum.timestamp,
                "Dimensions": [
                    {"Name": dimension.name, "Value": dimension.value}
                    for dimension in datum.dimensions
                ],
            }
            for datum in metric_data
        ],
    }


def write_metric_payload(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path

