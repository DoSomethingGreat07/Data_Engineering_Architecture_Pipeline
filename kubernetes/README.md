# Kubernetes Extension

This directory is an optional Kubernetes extension for repo-hosted services.

Important:
- This does not replace the required Docker-based architecture.
- It is provided as an additional deployment option for local platform services only.
- Databricks, Snowflake, Kinesis, and S3 remain external managed services.

Included manifests:
- namespace
- config map
- Airflow Postgres
- Airflow webserver
- Airflow scheduler
- platform dev shell deployment
- dbt job example

Run from `/Users/nikhiljuluri/Desktop/eureka/Production_Pipeline`:

```bash
kubectl apply -f kubernetes/base/
```

These manifests assume you will provide secrets separately before production-like use.

