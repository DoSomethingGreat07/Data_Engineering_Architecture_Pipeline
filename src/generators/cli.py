from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.common.config import load_settings
from src.common.logging_utils import configure_logging
from src.generators.synthetic_data import FinancialDataGenerator, write_datasets

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic financial data.")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file.")
    parser.add_argument(
        "--output-dir",
        required=False,
        help="Optional override for the generated dataset output directory.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.config)
    configure_logging(settings.app.log_level)

    output_dir = Path(args.output_dir or "data/generated")
    generator = FinancialDataGenerator(settings.generation)
    batch_datasets, stream_events, malformed_stream_events = generator.generate_all()
    paths = write_datasets(
        output_dir,
        batch_datasets,
        stream_events,
        malformed_stream_events,
    )
    LOGGER.info(
        "synthetic data generation complete",
        extra={
            "output_dir": str(output_dir),
            "stream_events_path": str(paths.stream_events_jsonl),
            "malformed_events_path": str(paths.malformed_stream_events_jsonl),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
