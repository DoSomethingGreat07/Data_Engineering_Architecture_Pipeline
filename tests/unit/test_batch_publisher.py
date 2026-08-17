from pathlib import Path

from src.batch_publisher.s3_sync import iter_publishable_files, publish_directory


class FakeS3Client:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        self.uploads.append((filename, bucket, key))


def test_iter_publishable_files_skips_crc_and_hidden_files(tmp_path: Path) -> None:
    root = tmp_path / "silver"
    (root / "_delta_log").mkdir(parents=True)
    (root / "processing_date=2026-08-16").mkdir(parents=True)
    (root / "_delta_log" / "00000000000000000000.json").write_text("{}", encoding="utf-8")
    (root / "_delta_log" / ".00000000000000000000.json.crc").write_text("", encoding="utf-8")
    (root / "processing_date=2026-08-16" / "part-00000.snappy.parquet").write_text(
        "x",
        encoding="utf-8",
    )
    (root / "processing_date=2026-08-16" / ".part-00000.snappy.parquet.crc").write_text(
        "",
        encoding="utf-8",
    )

    files = iter_publishable_files(root)

    assert [path.relative_to(root).as_posix() for path in files] == [
        "_delta_log/00000000000000000000.json",
        "processing_date=2026-08-16/part-00000.snappy.parquet",
    ]


def test_publish_directory_uploads_relative_paths(tmp_path: Path) -> None:
    root = tmp_path / "gold"
    (root / "fact_transaction" / "_delta_log").mkdir(parents=True)
    target_file = root / "fact_transaction" / "_delta_log" / "00000000000000000000.json"
    target_file.write_text("{}", encoding="utf-8")
    client = FakeS3Client()

    published = publish_directory(
        s3_client=client,
        bucket="fdp-bucket",
        local_root=root,
        s3_prefix="batch/gold",
    )

    assert len(published) == 1
    assert published[0].s3_key == "batch/gold/fact_transaction/_delta_log/00000000000000000000.json"
    assert client.uploads == [
        (
            str(target_file),
            "fdp-bucket",
            "batch/gold/fact_transaction/_delta_log/00000000000000000000.json",
        )
    ]
