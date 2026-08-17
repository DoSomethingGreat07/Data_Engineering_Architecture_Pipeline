from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class S3UploadClientProtocol(Protocol):
    def upload_file(self, Filename: str, Bucket: str, Key: str) -> None:  # noqa: N803
        ...


@dataclass(frozen=True)
class PublishedObject:
    local_path: Path
    s3_key: str


def iter_publishable_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not path.name.startswith(".") and not path.name.endswith(".crc")
    )


def publish_directory(
    *,
    s3_client: S3UploadClientProtocol,
    bucket: str,
    local_root: Path,
    s3_prefix: str,
) -> list[PublishedObject]:
    published: list[PublishedObject] = []
    for file_path in iter_publishable_files(local_root):
        relative_path = file_path.relative_to(local_root).as_posix()
        s3_key = "/".join(part.strip("/") for part in [s3_prefix, relative_path] if part)
        s3_client.upload_file(str(file_path), bucket, s3_key)
        published.append(PublishedObject(local_path=file_path, s3_key=s3_key))
    return published
