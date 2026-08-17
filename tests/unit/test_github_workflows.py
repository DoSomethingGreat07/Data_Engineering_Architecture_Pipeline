from pathlib import Path

import yaml


def test_pr_workflow_exists_and_has_jobs() -> None:
    workflow = yaml.safe_load(
        Path(".github/workflows/pr-validation.yml").read_text(encoding="utf-8")
    )
    assert workflow["name"] == "PR Validation"
    assert "python-quality" in workflow["jobs"]
    assert "terraform-validation" in workflow["jobs"]


def test_main_workflow_exists_and_has_plan_and_deploy_jobs() -> None:
    workflow = yaml.safe_load(
        Path(".github/workflows/main-deploy-plan.yml").read_text(encoding="utf-8")
    )
    assert workflow["name"] == "Main Branch Delivery"
    assert "terraform-plan" in workflow["jobs"]
    assert "deploy-application-code" in workflow["jobs"]

