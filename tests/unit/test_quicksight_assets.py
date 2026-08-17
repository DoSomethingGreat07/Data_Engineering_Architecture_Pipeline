from pathlib import Path


def test_quicksight_dashboard_spec_exists() -> None:
    assert Path("quicksight/dashboard_spec.md").exists()


def test_quicksight_readme_exists() -> None:
    assert Path("quicksight/README.md").exists()
