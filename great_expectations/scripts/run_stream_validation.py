from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.validation.gx_runner import load_dataframe_from_file, validate_pandas_dataframe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Great Expectations validation on a streaming micro-batch sample."
    )
    parser.add_argument("--suite-name", default="streaming_events_microbatch")
    parser.add_argument("--dataset-name", default="streaming_events")
    parser.add_argument("--stage", default="stream_microbatch")
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--input-dir", default=None)
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--result-output-dir", default="great_expectations/results")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_file = resolve_input_file(args.input_file, args.input_dir)
    dataframe = load_dataframe_from_file(input_file)
    required_columns = [
        "event_id",
        "event_type",
        "partition_key",
        "event_timestamp",
        "processing_timestamp",
        "currency_code",
        "transaction_status",
        "transaction_amount",
        "risk_score",
    ]
    dataframe = dataframe.reindex(columns=required_columns, fill_value=None)
    summary = validate_pandas_dataframe(
        ge_root=args.ge_root,
        suite_name=args.suite_name,
        dataframe=dataframe,
        datasource_name="financial_stream_datasource",
        asset_name=f"{args.dataset_name}_{args.stage}_asset",
        batch_definition_name=f"{args.dataset_name}_{args.stage}_batch",
        stage=args.stage,
        dataset_name=args.dataset_name,
        result_output_dir=args.result_output_dir,
    )
    return 0 if summary.success else 1


def resolve_input_file(input_file: str | None, input_dir: str | None) -> Path:
    if bool(input_file) == bool(input_dir):
        raise ValueError("use exactly one of --input-file or --input-dir")
    if input_file:
        return Path(input_file)
    candidates = sorted(Path(input_dir or "").glob("stream_events_*.json*"))
    if not candidates:
        raise FileNotFoundError(f"no streaming event files found under {input_dir}")
    return candidates[-1]


if __name__ == "__main__":
    raise SystemExit(main())
