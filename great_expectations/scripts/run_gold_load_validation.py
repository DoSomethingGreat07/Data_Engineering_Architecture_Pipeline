from __future__ import annotations

import argparse

import pandas as pd

from src.validation.gx_runner import validate_pandas_dataframe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Great Expectations validation on reconciliation summary data."
    )
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--result-output-dir", default="great_expectations/results")
    parser.add_argument("--max-row-count-difference", type=float, default=0)
    parser.add_argument("--max-debit-credit-difference", type=float, default=0.01)
    parser.add_argument("--max-duplicate-rate", type=float, default=0.05)
    parser.add_argument("--max-rejected-rate", type=float, default=0.10)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataframe = pd.read_json(args.input_file)
    summary = validate_pandas_dataframe(
        ge_root=args.ge_root,
        suite_name="gold_load_validation",
        dataframe=dataframe,
        datasource_name="financial_gold_datasource",
        asset_name="gold_reconciliation_asset",
        batch_definition_name="gold_reconciliation_batch",
        stage="gold_load",
        dataset_name="gold_reconciliation",
        result_output_dir=args.result_output_dir,
        expectation_parameters={
            "max_row_count_difference": args.max_row_count_difference,
            "max_debit_credit_difference": args.max_debit_credit_difference,
            "max_duplicate_rate": args.max_duplicate_rate,
            "max_rejected_rate": args.max_rejected_rate,
        },
    )
    return 0 if summary.success else 1


if __name__ == "__main__":
    raise SystemExit(main())

