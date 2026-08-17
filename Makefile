SHELL := /bin/bash
PYTHON ?= python3.11
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy

.PHONY: setup lint format type-check test generate-data validate-all clean airflow-up airflow-down dbt-compile terraform-validate

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements/development.txt

lint:
	$(RUFF) check src tests scripts

format:
	$(RUFF) format src tests scripts

type-check:
	$(MYPY) src

test:
	$(PYTEST)

generate-data:
	$(VENV)/bin/python -m src.generators.cli --config config/development.yaml --output-dir data/generated

ingest-sample-batch:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after setting a real bucket and AWS access:"
	@echo ".venv/bin/python -m src.batch_producer.cli --bucket <bucket> --file data/generated/batch/transactions_YYYYMMDDTHHMMSSZ.json --aws-region us-east-1 --aws-profile default"

ingest-extracted-batch:
	@echo "Upload the latest extracted canonical batch files to S3 Bronze after Terraform creates the data lake bucket:"
	@echo ".venv/bin/python -m src.batch_producer.cli --bucket <bucket> --input-dir data/external_sources/canonical --latest-only --aws-region us-east-1 --aws-profile default"

publish-sample-stream:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after setting a real Kinesis stream and AWS access:"
	@echo ".venv/bin/python -m src.stream_producer.cli --stream-name <stream-name> --events-file data/generated/streaming/events.jsonl --aws-region us-east-1 --aws-profile default --finite-event-count 25"

plaid-batch-extract:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after setting .env Plaid values:"
	@echo ".venv/bin/python -m src.sources.plaid_batch.cli --customer-id CUST-NFCU-001 --full-name 'Navy Federal Member' --email member@example.com"

plaid-search-institution:
	@echo "Search institutions by name:"
	@echo ".venv/bin/python -m src.sources.plaid_batch.cli --customer-id CUST-NFCU-001 --full-name 'Navy Federal Member' --email member@example.com --search-institution 'Navy Federal Credit Union'"

plaid-create-link-token:
	@echo "Create a Plaid Link token for real institution login:"
	@echo ".venv/bin/python -m src.sources.plaid_batch.cli --customer-id CUST-NFCU-001 --full-name 'Navy Federal Member' --email member@example.com --create-link-token-only"

plaid-sandbox-seeded-token:
	@echo "Create a Plaid sandbox token and seed demo transactions:"
	@echo ".venv/bin/python -m src.sources.plaid_batch.cli --customer-id CUST-NFCU-001 --full-name 'Navy Federal Member' --email member@example.com --create-sandbox-token-only --seed-sandbox-transactions"

alpha-vantage-batch-extract:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after setting .env Alpha Vantage values:"
	@echo ".venv/bin/python -m src.sources.alpha_vantage_batch.cli --symbols AAPL,MSFT,VOO --daily-outputsize compact"

alpaca-stream-capture:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after setting .env Alpaca values:"
	@echo ".venv/bin/python -m src.sources.alpaca_streaming.cli --symbols AAPL,MSFT --max-messages 25 --output-dir data/external_sources"

gx-bootstrap:
	$(VENV)/bin/python great_expectations/scripts/bootstrap_context.py

gx-validate-batch:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline:"
	@echo ".venv/bin/python great_expectations/scripts/run_batch_validation.py --suite-name transactions_bronze --dataset-name transactions --stage bronze_post_ingest --input-file data/generated/batch/ingest_ready/transactions_20260815T120000Z.json"

gx-validate-stream:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline:"
	@echo ".venv/bin/python great_expectations/scripts/run_stream_validation.py --input-file data/generated/streaming/events.jsonl"

gx-validate-extracted-batch:
	@echo "Validate the latest extracted canonical batch files with Great Expectations:"
	@echo ".venv/bin/python great_expectations/scripts/run_extracted_batch_validations.py --input-dir data/external_sources/canonical --latest-only"

stage-plaid-batch:
	@echo "Stage the latest extracted Plaid canonical files into local Bronze layout for Spark:"
	@echo ".venv/bin/python -m src.batch_preparation.cli --canonical-root data/external_sources/canonical --bronze-root data/lakehouse/batch/raw"

run-local-batch-pipeline:
	@echo "Run the local Spark batch pipeline after staging Bronze data and using a compatible Java runtime:"
	@echo ".venv/bin/python -m databricks.batch.financial_batch_pipeline --bronze-root data/lakehouse/batch/raw --silver-root data/lakehouse/batch/silver --gold-root data/lakehouse/batch/gold --rejected-root data/lakehouse/batch/rejected --disable-ge-validation"

publish-local-batch-to-s3:
	@echo "Upload the local Silver/Gold/Rejected Delta outputs to S3:"
	@echo ".venv/bin/python -m src.batch_publisher.cli --bucket <bucket> --aws-region us-east-1 --aws-profile default"

validate-all: lint type-check test

airflow-up:
	docker compose up -d airflow-postgres airflow-webserver airflow-scheduler

airflow-down:
	docker compose down

dbt-compile:
	docker compose run --rm dbt dbt compile --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial

dbt-parse:
	docker compose run --rm dbt dbt parse --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial

quicksight-handoff:
	@echo "Generate QuickSight Athena handoff assets after dbt reporting marts exist:"
	@echo ".venv/bin/python -m src.quicksight_handoff.cli --output-dir quicksight/output --catalog awsdatacatalog --schema fdp_dev_batch_analytics --workgroup primary --staging-dir s3://<bucket>/athena/results/ --aws-region us-east-1 --aws-profile default --quicksight-region us-east-1"

dev-shell:
	./scripts/dev_shell.sh

airflow-init:
	./scripts/airflow_init.sh

dbt-deps:
	docker compose run --rm dbt dbt deps --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial

docker-validate:
	docker compose config > /dev/null

docker-test:
	docker compose run --rm tests

terraform-validate:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after copying terraform/environments/dev/terraform.tfvars.example to terraform.tfvars:"
	@echo "terraform -chdir=terraform/environments/dev fmt -check -recursive"
	@echo "terraform -chdir=terraform/environments/dev init"
	@echo "terraform -chdir=terraform/environments/dev validate"
	@echo "terraform -chdir=terraform/environments/dev plan -var-file=terraform.tfvars"

terraform-s3-only-validate:
	@echo "Run from /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline after copying terraform/environments/s3_only/terraform.tfvars.example to terraform.tfvars:"
	@echo "terraform -chdir=terraform/environments/s3_only fmt -check -recursive"
	@echo "terraform -chdir=terraform/environments/s3_only init"
	@echo "terraform -chdir=terraform/environments/s3_only validate"
	@echo "terraform -chdir=terraform/environments/s3_only plan -var-file=terraform.tfvars"

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage data/generated
