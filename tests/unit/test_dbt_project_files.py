from pathlib import Path

import yaml


def test_dbt_project_config_exists_and_has_expected_name() -> None:
    project = yaml.safe_load(Path("dbt_financial/dbt_project.yml").read_text(encoding="utf-8"))
    assert project["name"] == "dbt_financial"
    assert project["profile"] == "dbt_financial"


def test_dbt_sources_file_contains_lakehouse_source() -> None:
    sources = yaml.safe_load(Path("dbt_financial/models/sources.yml").read_text(encoding="utf-8"))
    assert sources["sources"][0]["name"] == "lakehouse"
