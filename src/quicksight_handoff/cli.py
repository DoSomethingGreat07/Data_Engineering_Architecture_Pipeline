from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError

REPORTING_OBJECTS: dict[str, dict[str, dict[str, str]]] = {
    "batch": {
        "mart_financial_performance": {
            "dashboard_name": "Financial Performance",
            "description": "Daily transaction performance by processing date and currency.",
        },
        "mart_customer_risk": {
            "dashboard_name": "Customer Risk",
            "description": "Customer-level risk and transaction concentration summary.",
        },
        "mart_regulatory_reconciliation": {
            "dashboard_name": "Regulatory Reconciliation",
            "description": "Debit versus credit imbalance monitoring for batch controls.",
        },
    },
    "streaming": {
        "mart_stream_trade_performance": {
            "dashboard_name": "Streaming Trade Performance",
            "description": "Realtime-style trade notional, count, and pricing trends by symbol and side.",
        },
        "mart_stream_customer_exposure": {
            "dashboard_name": "Streaming Customer Exposure",
            "description": "Customer and account level exposure built from realtime trade events.",
        },
        "mart_stream_reconciliation": {
            "dashboard_name": "Streaming Reconciliation",
            "description": "Accepted versus rejected streaming event monitoring and rejection ratio controls.",
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate QuickSight handoff assets from Athena/Glue reporting marts.",
    )
    parser.add_argument("--output-dir", default="quicksight/output")
    parser.add_argument("--catalog", default="awsdatacatalog")
    parser.add_argument("--schema", default="fdp_dev_batch_analytics")
    parser.add_argument("--workgroup", default="primary")
    parser.add_argument("--staging-dir", default="")
    parser.add_argument("--mode", choices=["batch", "streaming"], default="batch")
    parser.add_argument("--aws-region", default="us-east-1")
    parser.add_argument("--aws-profile", default="default")
    parser.add_argument("--quicksight-region", default="us-east-1")
    return parser.parse_args()


def fetch_glue_table_metadata(
    *,
    database_name: str,
    mode: str,
    aws_region: str,
    aws_profile: str,
) -> list[dict[str, Any]]:
    session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
    glue = session.client("glue")
    tables: list[dict[str, Any]] = []
    for table_name, dashboard in REPORTING_OBJECTS[mode].items():
        response = glue.get_table(DatabaseName=database_name, Name=table_name)
        table = response["Table"]
        columns = table["StorageDescriptor"].get("Columns", [])
        tables.append(
            {
                "table_name": table_name,
                "dashboard_name": dashboard["dashboard_name"],
                "description": dashboard["description"],
                "location": table["StorageDescriptor"].get("Location", ""),
                "columns": [
                    {"name": column["Name"], "type": column["Type"]}
                    for column in columns
                ],
            }
        )
    return tables


def fallback_table_metadata(mode: str) -> list[dict[str, Any]]:
    return [
        {
            "table_name": table_name,
            "dashboard_name": dashboard["dashboard_name"],
            "description": dashboard["description"],
            "location": "",
            "columns": [],
        }
        for table_name, dashboard in REPORTING_OBJECTS[mode].items()
    ]


def build_manifest(
    *,
    mode: str,
    catalog: str,
    schema: str,
    workgroup: str,
    staging_dir: str,
    quicksight_region: str,
    tables: list[dict[str, Any]],
) -> dict[str, Any]:
    mart_schema = f"{schema}_marts"
    dataset_noun = "three reporting datasets" if mode == "batch" else "three streaming reporting datasets"
    return {
        "service": "Amazon QuickSight",
        "connector": "Amazon Athena",
        "mode": mode,
        "catalog": catalog,
        "database": mart_schema,
        "workgroup": workgroup,
        "staging_dir": staging_dir,
        "quicksight_region": quicksight_region,
        "datasets": tables,
        "quicksight_setup_steps": [
            "Open Amazon QuickSight and create or access a QuickSight account in the target AWS region.",
            "In Manage QuickSight -> Security & permissions, enable Amazon Athena and the required S3 buckets.",
            "If Glue Data Catalog access is needed, enable the AWS Glue Data Catalog connector.",
            f"Create Athena-backed datasets using catalog '{catalog}' and database '{mart_schema}'.",
            f"Use workgroup '{workgroup}' and the configured Athena query result location.",
            f"Build analyses and publish dashboards from the {dataset_noun} listed in this manifest.",
        ],
    }


def write_outputs(output_dir: Path, manifest: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "quicksight_connection_manifest.json"
    setup_path = output_dir / "quicksight_setup_summary.md"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    dataset_lines = []
    for dataset in manifest["datasets"]:
        columns = ", ".join(column["name"] for column in dataset["columns"])
        dataset_lines.append(
            "\n".join(
                [
                    f"## {dataset['dashboard_name']}",
                    f"- Dataset table: `{dataset['table_name']}`",
                    f"- Description: {dataset['description']}",
                    f"- Location: `{dataset['location']}`",
                    f"- Columns: {columns}",
                ]
            )
        )

    setup_path.write_text(
        "\n".join(
            [
                "# QuickSight Athena Handoff",
                "",
                f"- Service: `{manifest['service']}`",
                f"- Connector: `{manifest['connector']}`",
                f"- Catalog: `{manifest['catalog']}`",
                f"- Database: `{manifest['database']}`",
                f"- Workgroup: `{manifest['workgroup']}`",
                f"- Query result staging dir: `{manifest['staging_dir']}`",
                f"- QuickSight region: `{manifest['quicksight_region']}`",
                "",
                "## Setup Steps",
                *[f"- {step}" for step in manifest["quicksight_setup_steps"]],
                "",
                "## Datasets",
                *dataset_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    mart_database = f"{args.schema}_marts"
    try:
        tables = fetch_glue_table_metadata(
            database_name=mart_database,
            mode=args.mode,
            aws_region=args.aws_region,
            aws_profile=args.aws_profile,
        )
    except (BotoCoreError, ClientError, EndpointConnectionError):
        tables = fallback_table_metadata(args.mode)
    manifest = build_manifest(
        mode=args.mode,
        catalog=args.catalog,
        schema=args.schema,
        workgroup=args.workgroup,
        staging_dir=args.staging_dir,
        quicksight_region=args.quicksight_region,
        tables=tables,
    )
    write_outputs(Path(args.output_dir), manifest)
    print(json.dumps({"output_dir": args.output_dir, "database": mart_database}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
