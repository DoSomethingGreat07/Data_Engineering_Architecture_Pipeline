from pathlib import Path

import yaml


def test_kubernetes_namespace_manifest_exists() -> None:
    manifest = yaml.safe_load(
        Path("kubernetes/base/00-namespace.yaml").read_text(encoding="utf-8")
    )
    assert manifest["kind"] == "Namespace"


def test_kubernetes_job_manifest_exists() -> None:
    manifest = yaml.safe_load(
        Path("kubernetes/base/06-dbt-job.yaml").read_text(encoding="utf-8")
    )
    assert manifest["kind"] == "Job"

