# GitHub Deployment Prep

This repository is ready to publish after keeping local-only runtime files out of version control.

## Safe To Commit

- Source code under `src/`
- Airflow DAGs, Dockerfiles, scripts, and tests
- Terraform modules and environment `*.example` files
- dbt models, macros, seeds, and docs
- Great Expectations suite specs under `great_expectations/expectations/`
- QuickSight documentation under `quicksight/`

## Do Not Commit

- `.env`
- `dbt_financial/profiles.yml`
- Terraform state files and live `terraform.tfvars`
- Generated data under `data/external_sources/` and `data/lakehouse/`
- Generated reports under `reports/`
- Generated QuickSight manifests under `quicksight/output/` and `quicksight/streaming_output/`
- Great Expectations runtime artifacts under `great_expectations/gx/uncommitted/` and `great_expectations/results/`
- Local virtualenv, caches, logs, and PID files

## First GitHub Push

If this folder is not yet a standalone git repository:

```bash
cd /Users/nikhiljuluri/Desktop/eureka/Production_Pipeline
git init
git add .
git status
```

Review `git status` and confirm no secrets, state files, or generated runtime artifacts are staged.

Then create the first commit:

```bash
git commit -m "Initial commit: financial data platform"
```

Add your GitHub remote and push:

```bash
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Before Public Push

- Rotate any credentials that were previously pasted into chat or local files.
- Keep `.env` local only and share only `.env.example`.
- Keep `terraform.tfvars` local only and share only `terraform.tfvars.example`.
