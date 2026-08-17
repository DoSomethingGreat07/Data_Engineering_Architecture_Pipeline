from pathlib import Path

from src.common.env_utils import load_env_file


def test_load_env_file_handles_spaces_and_quotes(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        'PLAID_CLIENT_ID=abc123\nSEC_USER_AGENT="Your Name your_email@example.com"\n',
        encoding="utf-8",
    )
    values = load_env_file(env_path)
    assert values["PLAID_CLIENT_ID"] == "abc123"
    assert values["SEC_USER_AGENT"] == "Your Name your_email@example.com"
