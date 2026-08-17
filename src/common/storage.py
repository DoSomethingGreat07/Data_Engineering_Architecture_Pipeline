from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class S3DataLakePaths:
    bucket: str
    batch_raw_prefix: str
    batch_rejected_prefix: str
    batch_silver_prefix: str
    batch_gold_prefix: str
    streaming_raw_prefix: str
    streaming_rejected_prefix: str
    streaming_silver_prefix: str
    streaming_gold_prefix: str
    streaming_checkpoint_prefix: str

    def batch_raw_key(self, dataset_name: str, filename: str) -> str:
        return self._join(self.batch_raw_prefix, dataset_name, filename)

    def batch_raw_metadata_key(self, dataset_name: str, filename: str) -> str:
        return self._join(self.batch_raw_prefix, dataset_name, "_metadata", filename)

    def batch_rejected_key(self, dataset_name: str, filename: str) -> str:
        return self._join(self.batch_rejected_prefix, dataset_name, filename)

    def silver_table_path(self, table_name: str) -> str:
        return self._join(self.batch_silver_prefix, table_name)

    def gold_table_path(self, table_name: str) -> str:
        return self._join(self.batch_gold_prefix, table_name)

    def _join(self, *parts: str) -> str:
        return "/".join(part.strip("/") for part in parts if part)
