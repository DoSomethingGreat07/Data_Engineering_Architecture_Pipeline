# Terraform Phase 2

This directory contains the reusable AWS foundation for the financial data platform.

Phase 2 scope:
- S3 data lake bucket and logical prefixes
- Kinesis Data Stream
- Glue Data Catalog database
- KMS customer-managed key
- IAM runtime and deployment roles
- VPC, private subnets, and VPC endpoints
- CloudWatch log groups and alarms

Important:
- Do not run `terraform apply` without explicit approval.
- Use `terraform plan` only for review.
- Clean up any applied resources with `terraform destroy` to avoid ongoing charges.

## S3-only Option

If you want to work only on the batch landing layer plus Great Expectations, use
`terraform/environments/s3_only/`.

This environment creates only:
- one S3 batch data lake bucket
- one Glue Data Catalog database
- Glue catalog Delta table registrations for active Silver and Gold datasets
- versioning
- server-side encryption using `AES256`
- four batch prefixes:
  - `batch/raw/`
  - `batch/rejected/`
  - `batch/silver/`
  - `batch/gold/`

Example commands:

```bash
cp terraform/environments/s3_only/terraform.tfvars.example terraform/environments/s3_only/terraform.tfvars
terraform -chdir=terraform/environments/s3_only init
terraform -chdir=terraform/environments/s3_only plan -var-file=terraform.tfvars
terraform -chdir=terraform/environments/s3_only apply -var-file=terraform.tfvars
```

After that, validate extracted batch files locally with Great Expectations:

```bash
.venv/bin/python great_expectations/scripts/run_extracted_batch_validations.py \
  --input-dir data/external_sources/canonical \
  --latest-only
```

Validation commands from `/Users/nikhiljuluri/Desktop/eureka/Production_Pipeline`:

```bash
terraform -chdir=terraform/environments/dev fmt -check -recursive
terraform -chdir=terraform/environments/dev init
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev plan -var-file=terraform.tfvars
```

Optional checks:

```bash
tflint --chdir terraform/environments/dev
tfsec terraform/environments/dev
```

## Batch Usage After Terraform

After you install Terraform, apply the `dev` stack, and obtain the bucket output, the batch path for this project is:

1. Extract canonical batch data locally
   - Plaid sandbox/demo batch under `data/external_sources/canonical/plaid/`
   - Alpha Vantage batch under `data/external_sources/canonical/alpha_vantage/`
2. Upload the latest canonical files into the S3 Bronze raw prefix created by Terraform
3. Trigger the downstream Databricks batch pipeline against the Bronze objects

Example upload command from `/Users/nikhiljuluri/Desktop/eureka/Production_Pipeline`:

```bash
.venv/bin/python -m src.batch_producer.cli \
  --bucket <terraform-output-bucket> \
  --input-dir data/external_sources/canonical \
  --latest-only \
  --aws-region us-east-1 \
  --aws-profile default
```

This command uploads the latest timestamped file for each supported dataset such as `customers`, `accounts`, `transactions`, and `securities` into `batch/raw/<dataset>/`.
