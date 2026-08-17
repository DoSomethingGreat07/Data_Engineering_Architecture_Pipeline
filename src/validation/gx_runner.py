from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

import great_expectations as gx
import great_expectations.expectations as gxe
from src.validation.models import SuiteSpec, ValidationSummary, suite_spec_path
from src.validation.reporting import (
    build_cloudwatch_metric_payload,
    write_metric_payload,
    write_validation_summary,
)


def get_file_context(ge_root: str | Path) -> Any:
    root = Path(ge_root)
    root.mkdir(parents=True, exist_ok=True)
    return gx.get_context(mode="file", project_root_dir=str(root))


def load_suite_spec(ge_root: str | Path, suite_name: str) -> SuiteSpec:
    path = suite_spec_path(ge_root, suite_name)
    return SuiteSpec.model_validate_json(path.read_text(encoding="utf-8"))


def build_expectation_suite(spec: SuiteSpec) -> Any:
    suite = gx.ExpectationSuite(spec.suite_name)
    for expectation_spec in spec.expectations:
        expectation_class = getattr(gxe, expectation_spec.expectation_type)
        suite.add_expectation(expectation_class(**expectation_spec.kwargs))
    return suite


def ensure_suite(context: Any, spec: SuiteSpec) -> Any:
    suite = build_expectation_suite(spec)
    for _ in range(2):
        try:
            try:
                existing = context.suites.get(spec.suite_name)
                context.suites.delete(spec.suite_name)
                del existing
            except Exception as exc:  # noqa: BLE001
                if _is_corrupt_suite_error(exc):
                    _delete_corrupt_suite_file(context, spec.suite_name)
                else:
                    pass
            return context.suites.add(suite)
        except Exception as exc:  # noqa: BLE001
            if _is_corrupt_suite_error(exc):
                _delete_corrupt_suite_file(context, spec.suite_name)
                continue
            raise
    return context.suites.add(suite)


def validate_pandas_dataframe(
    *,
    ge_root: str | Path,
    suite_name: str,
    dataframe: pd.DataFrame,
    datasource_name: str,
    asset_name: str,
    batch_definition_name: str,
    stage: str,
    dataset_name: str,
    result_output_dir: str | Path,
    expectation_parameters: dict[str, Any] | None = None,
) -> ValidationSummary:
    context = get_file_context(ge_root)
    suite_spec = load_suite_spec(ge_root, suite_name)
    suite = ensure_suite(context, suite_spec)

    try:
        datasource = context.data_sources.get(datasource_name)
    except Exception:  # noqa: BLE001
        datasource = context.data_sources.add_pandas(name=datasource_name)
    try:
        asset = datasource.get_asset(asset_name)
    except Exception:  # noqa: BLE001
        asset = datasource.add_dataframe_asset(name=asset_name)
    try:
        batch_definition = asset.get_batch_definition(batch_definition_name)
    except Exception:  # noqa: BLE001
        batch_definition = asset.add_batch_definition_whole_dataframe(batch_definition_name)

    validation_definition = gx.ValidationDefinition(
        name=f"{suite_name}_{stage}",
        data=batch_definition,
        suite=suite,
    )
    try:
        context.validation_definitions.get(validation_definition.name)
        context.validation_definitions.delete(validation_definition.name)
    except Exception:  # noqa: BLE001
        pass
    validation_definition = context.validation_definitions.add(validation_definition)
    result = validation_definition.run(
        batch_parameters={"dataframe": dataframe},
        expectation_parameters=expectation_parameters,
    )
    result_path = (
        Path(result_output_dir)
        / stage
        / f"{dataset_name}_{suite_name}_validation_result.json"
    )
    summary = ValidationSummary.create(
        suite_name=suite_name,
        success=bool(result.success),
        statistics=result.statistics,
        stage=stage,
        dataset_name=dataset_name,
        result_path=str(result_path),
    )
    write_validation_summary(result_path, summary)
    metric_path = result_path.with_name(result_path.stem + "_cloudwatch_metric.json")
    write_metric_payload(metric_path, build_cloudwatch_metric_payload(summary))
    return summary


def validate_spark_dataframe(
    *,
    ge_root: str | Path,
    suite_name: str,
    dataframe: Any,
    datasource_name: str,
    asset_name: str,
    batch_definition_name: str,
    stage: str,
    dataset_name: str,
    result_output_dir: str | Path,
    expectation_parameters: dict[str, Any] | None = None,
) -> ValidationSummary:
    context = get_file_context(ge_root)
    suite_spec = load_suite_spec(ge_root, suite_name)
    suite = ensure_suite(context, suite_spec)

    try:
        datasource = context.data_sources.get(datasource_name)
    except Exception:  # noqa: BLE001
        datasource = context.data_sources.add_spark(name=datasource_name)
    try:
        asset = datasource.get_asset(asset_name)
    except Exception:  # noqa: BLE001
        asset = datasource.add_dataframe_asset(name=asset_name)
    try:
        batch_definition = asset.get_batch_definition(batch_definition_name)
    except Exception:  # noqa: BLE001
        batch_definition = asset.add_batch_definition_whole_dataframe(batch_definition_name)

    validation_definition = gx.ValidationDefinition(
        name=f"{suite_name}_{stage}",
        data=batch_definition,
        suite=suite,
    )
    try:
        context.validation_definitions.get(validation_definition.name)
        context.validation_definitions.delete(validation_definition.name)
    except Exception:  # noqa: BLE001
        pass
    validation_definition = context.validation_definitions.add(validation_definition)
    result = validation_definition.run(
        batch_parameters={"dataframe": dataframe},
        expectation_parameters=expectation_parameters,
    )
    result_path = (
        Path(result_output_dir)
        / stage
        / f"{dataset_name}_{suite_name}_validation_result.json"
    )
    summary = ValidationSummary.create(
        suite_name=suite_name,
        success=bool(result.success),
        statistics=result.statistics,
        stage=stage,
        dataset_name=dataset_name,
        result_path=str(result_path),
    )
    write_validation_summary(result_path, summary)
    metric_path = result_path.with_name(result_path.stem + "_cloudwatch_metric.json")
    write_metric_payload(metric_path, build_cloudwatch_metric_payload(summary))
    return summary


def load_dataframe_from_file(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)
    if file_path.suffix.lower() == ".json":
        return pd.read_json(file_path)
    if file_path.suffix.lower() == ".jsonl":
        return pd.read_json(file_path, lines=True)
    raise ValueError(f"unsupported validation input format: {file_path.suffix}")


def bootstrap_context_directory(ge_root: str | Path) -> Path:
    root = Path(ge_root)
    context = get_file_context(root)
    try:
        context.add_data_docs_site(
            site_name="local_site",
            site_config={
                "class_name": "SiteBuilder",
                "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
                "store_backend": {
                    "class_name": "TupleFilesystemStoreBackend",
                    "base_directory": "uncommitted/data_docs/local_site",
                },
            },
        )
    except Exception:  # noqa: BLE001
        pass
    return root


def _is_corrupt_suite_error(exc: Exception) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, json.JSONDecodeError):
            return True
        current = current.__cause__ or current.__context__
    return False


def _delete_corrupt_suite_file(context: Any, suite_name: str) -> None:
    try:
        base_dir = Path(context.root_directory) / "gx" / "expectations"
    except Exception:  # noqa: BLE001
        return
    suite_path = base_dir / f"{suite_name}.json"
    if suite_path.exists():
        suite_path.unlink()
