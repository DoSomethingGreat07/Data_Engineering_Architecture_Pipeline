from __future__ import annotations

import argparse

from src.validation.gx_runner import load_dataframe_from_file, validate_pandas_dataframe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Great Expectations validation on a batch file."
    )
    parser.add_argument("--suite-name", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--result-output-dir", default="great_expectations/results")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataframe = load_dataframe_from_file(args.input_file)
    summary = validate_pandas_dataframe(
        ge_root=args.ge_root,
        suite_name=args.suite_name,
        dataframe=dataframe,
        datasource_name="financial_batch_datasource",
        asset_name=f"{args.dataset_name}_{args.stage}_asset",
        batch_definition_name=f"{args.dataset_name}_{args.stage}_batch",
        stage=args.stage,
        dataset_name=args.dataset_name,
        result_output_dir=args.result_output_dir,
    )
    return 0 if summary.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
