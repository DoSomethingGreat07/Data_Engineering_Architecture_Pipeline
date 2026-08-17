from pathlib import Path

from src.batch_producer.discovery import discover_batch_files


def test_discover_batch_files_finds_supported_files(tmp_path: Path) -> None:
    base = tmp_path / "canonical"
    plaid_dir = base / "plaid"
    plaid_dir.mkdir(parents=True)
    (plaid_dir / "transactions_20260815T120000Z.json").write_text("[]", encoding="utf-8")
    (plaid_dir / "ignore_me.txt").write_text("x", encoding="utf-8")

    found = discover_batch_files(base)

    assert [path.name for path in found] == ["transactions_20260815T120000Z.json"]


def test_discover_batch_files_latest_only_keeps_latest_per_dataset(tmp_path: Path) -> None:
    base = tmp_path / "canonical"
    plaid_dir = base / "plaid"
    plaid_dir.mkdir(parents=True)
    (plaid_dir / "transactions_20260815T120000Z.json").write_text("[]", encoding="utf-8")
    (plaid_dir / "transactions_20260815T130000Z.json").write_text("[]", encoding="utf-8")
    (plaid_dir / "accounts_20260815T125000Z.json").write_text("[]", encoding="utf-8")

    found = discover_batch_files(base, latest_only=True)

    assert [path.name for path in found] == [
        "accounts_20260815T125000Z.json",
        "transactions_20260815T130000Z.json",
    ]
