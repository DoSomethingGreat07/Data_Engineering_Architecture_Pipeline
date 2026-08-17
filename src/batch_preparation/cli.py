from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.batch_preparation.plaid_bronze_stage import stage_plaid_batch_for_processing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage extracted Plaid canonical data into Bronze layout for batch Spark runs."
    )
    parser.add_argument("--canonical-root", default="data/external_sources/canonical")
    parser.add_argument("--bronze-root", default="data/lakehouse/batch/raw")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    staged = stage_plaid_batch_for_processing(
        canonical_root=Path(args.canonical_root),
        bronze_root=Path(args.bronze_root),
    )
    print(
        json.dumps(
            [
                {
                    "dataset_name": item.dataset_name,
                    "output_path": str(item.output_path),
                    "record_count": item.record_count,
                }
                for item in staged
            ],
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
