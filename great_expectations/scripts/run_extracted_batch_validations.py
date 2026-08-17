from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate extracted canonical batch files with Great Expectations."
    )
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--latest-only", action="store_true")
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--result-output-dir", default="great_expectations/results")
    parser.add_argument("--stage", default="bronze_post_extract")
    return parser


def main() -> int:
    from src.batch_producer.discovery import discover_batch_files
    from src.validation.batch_suite_map import SUITE_BY_DATASET
    from src.validation.gx_runner import (
        load_dataframe_from_file,
        validate_pandas_dataframe,
    )

    args = build_parser().parse_args()
    files = discover_batch_files(args.input_dir, latest_only=args.latest_only)
    summaries: list[dict[str, object]] = []

    for path in files:
        dataset_name = path.name.split("_", 1)[0]
        suite_name = SUITE_BY_DATASET.get(dataset_name)
        if suite_name is None:
            continue
        summary = validate_pandas_dataframe(
            ge_root=args.ge_root,
            suite_name=suite_name,
            dataframe=load_dataframe_from_file(path),
            datasource_name="financial_batch_datasource",
            asset_name=f"{dataset_name}_{args.stage}_asset",
            batch_definition_name=f"{dataset_name}_{args.stage}_batch",
            stage=args.stage,
            dataset_name=dataset_name,
            result_output_dir=args.result_output_dir,
        )
        summaries.append(
            {
                "dataset_name": dataset_name,
                "suite_name": suite_name,
                "success": summary.success,
                "result_path": summary.result_path,
            }
        )

    print(json.dumps(summaries, indent=2))
    return 0 if all(item["success"] for item in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
