from pathlib import Path

from src.common.metrics import (
    MetricDatum,
    MetricDimension,
    build_metric_payload,
    write_metric_payload,
)


def test_build_metric_payload_includes_dimensions() -> None:
    payload = build_metric_payload(
        "FinancialDataPlatform",
        [
            MetricDatum(
                metric_name="BatchIngestionFailures",
                value=1,
                dimensions=[MetricDimension(name="Environment", value="dev")],
            )
        ],
    )
    assert payload["Namespace"] == "FinancialDataPlatform"
    assert payload["MetricData"][0]["Dimensions"][0]["Name"] == "Environment"


def test_write_metric_payload_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "metric.json"
    write_metric_payload(target, {"Namespace": "FinancialDataPlatform", "MetricData": []})
    assert target.exists()

