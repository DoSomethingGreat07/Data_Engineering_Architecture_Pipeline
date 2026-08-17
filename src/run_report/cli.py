from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate batch pipeline execution reports.")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--execution-date", required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--aws-region", default="us-east-1")
    parser.add_argument("--aws-profile", default="default")
    return parser.parse_args()


def _latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_records(path: Path | None) -> int | None:
    if path is None:
        return None
    payload = _load_json(path)
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("accounts", "transactions", "customers", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
    return None


def _latest_json_payload(directory: Path, pattern: str) -> tuple[Path | None, Any | None]:
    path = _latest_file(directory, pattern)
    if path is None:
        return None, None
    return path, _load_json(path)


def _bronze_snapshot(base_path: Path) -> dict[str, dict[str, Any]]:
    datasets: dict[str, dict[str, Any]] = {}
    if not base_path.exists():
        return datasets
    for dataset_dir in sorted(path for path in base_path.iterdir() if path.is_dir()):
        latest_path, payload = _latest_json_payload(dataset_dir, "*.json")
        record_count = None
        sample_fields: list[str] = []
        if isinstance(payload, list):
            record_count = len(payload)
            if payload and isinstance(payload[0], dict):
                sample_fields = sorted(payload[0].keys())[:8]
        elif isinstance(payload, dict):
            record_count = _count_records(latest_path)
            if payload:
                sample_fields = sorted(payload.keys())[:8]
        datasets[dataset_dir.name] = {
            "latest_file": str(latest_path) if latest_path else None,
            "record_count": record_count,
            "sample_fields": sample_fields,
        }
    return datasets


def _delta_table_metrics(dataset_dir: Path) -> dict[str, Any]:
    partition_dirs = sorted(dataset_dir.glob("processing_date=*"))
    latest_partition = partition_dirs[-1].name if partition_dirs else None
    delta_log = dataset_dir / "_delta_log"
    latest_json = None
    if delta_log.exists():
        json_files = sorted(delta_log.glob("*.json"))
        latest_json = json_files[-1] if json_files else None

    row_count = None
    file_count = None
    sample_columns: list[str] = []
    if latest_json is not None:
        for line in latest_json.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if "commitInfo" in entry:
                metrics = entry["commitInfo"].get("operationMetrics", {})
                if row_count is None and metrics.get("numOutputRows"):
                    row_count = int(metrics["numOutputRows"])
                if file_count is None and metrics.get("numFiles"):
                    file_count = int(metrics["numFiles"])
            if "add" in entry and entry["add"].get("stats"):
                stats = json.loads(entry["add"]["stats"])
                row_count = row_count or stats.get("numRecords")
                min_values = stats.get("minValues", {})
                if isinstance(min_values, dict):
                    sample_columns = sorted(min_values.keys())[:8]
                break

    return {
        "exists": True,
        "latest_partition": latest_partition,
        "row_count": row_count,
        "file_count": file_count,
        "has_delta_log": delta_log.exists(),
        "sample_columns": sample_columns,
    }


def _delta_snapshot(base_path: Path) -> dict[str, dict[str, Any]]:
    datasets: dict[str, dict[str, Any]] = {}
    if not base_path.exists():
        return datasets
    for dataset_dir in sorted(path for path in base_path.iterdir() if path.is_dir()):
        datasets[dataset_dir.name] = _delta_table_metrics(dataset_dir)
    return datasets


def _transformation_notes() -> list[dict[str, str]]:
    return [
        {
            "stage": "raw_to_bronze",
            "summary": (
                "Canonical Plaid JSON files are staged into batch raw folders for "
                "downstream Spark processing."
            ),
        },
        {
            "stage": "bronze_to_silver",
            "summary": (
                "Spark standardizes types, deduplicates records, and rejects "
                "invalid transactional rows into rejected Delta tables."
            ),
        },
        {
            "stage": "silver_to_gold",
            "summary": (
                "Spark builds curated dimensions and facts such as dim_customer, "
                "dim_account, fact_transaction, and fact_daily_account_balance."
            ),
        },
        {
            "stage": "gold_to_marts",
            "summary": (
                "dbt creates Athena reporting marts for financial performance, "
                "customer risk, and regulatory reconciliation."
            ),
        },
        {
            "stage": "marts_to_quicksight",
            "summary": (
                "QuickSight handoff assets describe the Athena connection and the "
                "reporting marts to visualize."
            ),
        },
    ]


def _dbt_summary() -> dict[str, Any]:
    run_results_path = Path("dbt_financial/target/run_results.json")
    if not run_results_path.exists():
        return {"available": False}
    payload = _load_json(run_results_path)
    results = payload.get("results", [])
    status_counts: dict[str, int] = {}
    for result in results:
        status = result.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "available": True,
        "generated_at": payload.get("metadata", {}).get("generated_at"),
        "result_count": len(results),
        "status_counts": status_counts,
    }


def _quicksight_summary() -> dict[str, Any]:
    manifest_path = Path("quicksight/output/quicksight_connection_manifest.json")
    setup_path = Path("quicksight/output/quicksight_setup_summary.md")
    if not manifest_path.exists():
        return {"available": False}
    manifest = _load_json(manifest_path)
    return {
        "available": True,
        "manifest_path": str(manifest_path),
        "setup_summary_path": str(setup_path),
        "dataset_count": len(manifest.get("datasets", [])),
        "dataset_tables": [dataset["table_name"] for dataset in manifest.get("datasets", [])],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    canonical_root = Path("data/external_sources/canonical/plaid")
    accounts_path = _latest_file(canonical_root, "accounts_*.json")
    transactions_path = _latest_file(canonical_root, "transactions_*.json")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_id": args.run_id,
        "execution_date": args.execution_date,
        "aws": {
            "bucket": args.bucket,
            "region": args.aws_region,
            "profile": args.aws_profile,
        },
        "source_extract": {
            "accounts_file": str(accounts_path) if accounts_path else None,
            "transactions_file": str(transactions_path) if transactions_path else None,
            "accounts_count": _count_records(accounts_path),
            "transactions_count": _count_records(transactions_path),
        },
        "stage_summary": {
            "bronze": _bronze_snapshot(Path("data/lakehouse/batch/raw")),
            "silver": _delta_snapshot(Path("data/lakehouse/batch/silver")),
            "gold": _delta_snapshot(Path("data/lakehouse/batch/gold")),
            "rejected": _delta_snapshot(Path("data/lakehouse/batch/rejected")),
            "transformation_notes": _transformation_notes(),
        },
        "lakehouse": {
            "silver": _delta_snapshot(Path("data/lakehouse/batch/silver")),
            "gold": _delta_snapshot(Path("data/lakehouse/batch/gold")),
            "rejected": _delta_snapshot(Path("data/lakehouse/batch/rejected")),
        },
        "dbt": _dbt_summary(),
        "quicksight": _quicksight_summary(),
    }


def _markdown_report(report: dict[str, Any]) -> str:
    source = report["source_extract"]
    dbt = report["dbt"]
    quicksight = report["quicksight"]

    silver_datasets = ", ".join(
        f"{name} ({details.get('row_count', 'n/a')} rows)"
        for name, details in sorted(report["stage_summary"]["silver"].items())
    )
    gold_datasets = ", ".join(
        f"{name} ({details.get('row_count', 'n/a')} rows)"
        for name, details in sorted(report["stage_summary"]["gold"].items())
    )
    rejected_datasets = ", ".join(
        f"{name} ({details.get('row_count', 'n/a')} rows)"
        for name, details in sorted(report["stage_summary"]["rejected"].items())
    )
    bronze_datasets = ", ".join(
        f"{name} ({details.get('record_count', 'n/a')} records)"
        for name, details in sorted(report["stage_summary"]["bronze"].items())
    )

    dbt_line = "Unavailable"
    if dbt.get("available"):
        dbt_line = (
            f"{dbt['result_count']} results, status counts: {dbt['status_counts']}"
        )

    quicksight_line = "Unavailable"
    if quicksight.get("available"):
        quicksight_line = ", ".join(quicksight["dataset_tables"])

    return "\n".join(
        [
            "# Latest Batch Run Summary",
            "",
            f"- Run ID: `{report['run_id']}`",
            f"- Execution date: `{report['execution_date']}`",
            f"- Generated at: `{report['generated_at']}`",
            f"- S3 bucket: `{report['aws']['bucket']}`",
            "",
            "## Source Extract",
            f"- Accounts file: `{source['accounts_file']}`",
            f"- Transactions file: `{source['transactions_file']}`",
            f"- Accounts count: `{source['accounts_count']}`",
            f"- Transactions count: `{source['transactions_count']}`",
            "",
            "## Stage Summary",
            f"- Bronze datasets: {bronze_datasets}",
            f"- Silver datasets: {silver_datasets}",
            f"- Gold datasets: {gold_datasets}",
            f"- Rejected datasets: {rejected_datasets}",
            "",
            "## Transformations",
            *[
                f"- {note['stage']}: {note['summary']}"
                for note in report["stage_summary"]["transformation_notes"]
            ],
            "",
            "## dbt",
            f"- Summary: {dbt_line}",
            "",
            "## QuickSight",
            f"- Dataset objects: {quicksight_line}",
            f"- Setup summary: `{quicksight.get('setup_summary_path', '')}`",
            "",
        ]
    )


def write_outputs(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_json = output_dir / "latest_batch_run_summary.json"
    latest_md = output_dir / "latest_batch_run_summary.md"
    run_safe = report["run_id"].replace(":", "_").replace("/", "_")
    historical_json = output_dir / f"batch_run_summary_{run_safe}.json"

    payload = json.dumps(report, indent=2) + "\n"
    latest_json.write_text(payload, encoding="utf-8")
    historical_json.write_text(payload, encoding="utf-8")
    latest_md.write_text(_markdown_report(report), encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    write_outputs(Path(args.output_dir), report)
    print(json.dumps({"report_dir": args.output_dir, "run_id": args.run_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
