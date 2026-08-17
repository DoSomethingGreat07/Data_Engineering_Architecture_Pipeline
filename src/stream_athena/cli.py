from __future__ import annotations

import argparse
import json
import time

import boto3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a realtime Athena smoke-test query against the isolated "
            "streaming Glue database."
        )
    )
    parser.add_argument("--database-name", required=True)
    parser.add_argument("--aws-region", required=True)
    parser.add_argument("--aws-profile", default=None)
    parser.add_argument("--workgroup", default="primary")
    parser.add_argument("--staging-dir", required=True)
    parser.add_argument(
        "--repair-tables",
        nargs="*",
        default=[
            "silver_trades",
            "rejected_stream_events",
            "gold_fact_trade",
            "gold_trade_minute_metrics",
            "gold_customer_trade_exposure",
        ],
    )
    parser.add_argument(
        "--query",
        default=(
            "SELECT processing_date, COUNT(*) AS trade_count, "
            "SUM(transaction_amount) AS total_notional "
            "FROM gold_fact_trade GROUP BY 1 ORDER BY 1 DESC LIMIT 10"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    session_kwargs: dict[str, str] = {"region_name": args.aws_region}
    if args.aws_profile:
        session_kwargs["profile_name"] = args.aws_profile
    session = boto3.Session(**session_kwargs)
    athena = session.client("athena")
    repair_results = []
    for table_name in args.repair_tables:
        repair_query = f"MSCK REPAIR TABLE {table_name}"
        repair_execution_id, repair_state = execute_athena_query(
            athena=athena,
            query=repair_query,
            database_name=args.database_name,
            workgroup=args.workgroup,
            staging_dir=args.staging_dir,
        )
        repair_results.append(
            {
                "table_name": table_name,
                "query_execution_id": repair_execution_id,
                "state": repair_state,
            }
        )

    execution_id, state = execute_athena_query(
        athena=athena,
        query=args.query,
        database_name=args.database_name,
        workgroup=args.workgroup,
        staging_dir=args.staging_dir,
    )
    result = athena.get_query_results(QueryExecutionId=execution_id)
    rows = result["ResultSet"]["Rows"]
    print(
        json.dumps(
            {
                "repair_results": repair_results,
                "query_execution_id": execution_id,
                "state": state,
                "rows": rows[:10],
            },
            indent=2,
            default=str,
        )
    )
    return 0


def execute_athena_query(
    *,
    athena: object,
    query: str,
    database_name: str,
    workgroup: str,
    staging_dir: str,
) -> tuple[str, str]:
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database_name},
        WorkGroup=workgroup,
        ResultConfiguration={"OutputLocation": staging_dir},
    )
    execution_id = response["QueryExecutionId"]

    state = "QUEUED"
    while state in {"QUEUED", "RUNNING"}:
        time.sleep(2)
        status = athena.get_query_execution(QueryExecutionId=execution_id)
        state = status["QueryExecution"]["Status"]["State"]
    if state != "SUCCEEDED":
        raise RuntimeError(f"Athena query failed with state {state}: {query}")
    return execution_id, state


if __name__ == "__main__":
    raise SystemExit(main())
