# dbt Financial

This is the dbt Core project for Athena and Glue analytics modeling on top of the
S3 Delta lakehouse.

Run from `/Users/nikhiljuluri/Desktop/eureka/Production_Pipeline` after configuring AWS
credentials and a dbt Athena profile:

```bash
cp dbt_financial/profiles.yml.example dbt_financial/profiles.yml
docker compose build dbt
docker compose run --rm dbt dbt deps --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial
docker compose run --rm dbt dbt parse --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial
docker compose run --rm dbt dbt compile --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial
docker compose run --rm dbt dbt test --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial
DBT_TARGET=streaming docker compose run --rm dbt dbt run --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial --select tag:streaming
DBT_TARGET=streaming docker compose run --rm dbt dbt test --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial --select tag:streaming
```

Notes:
- The dbt container mounts your local `~/.aws` directory read-only so `AWS_PROFILE=default`
  can resolve the same credentials that work on your host machine.
- If you prefer not to use `AWS_PROFILE`, you can instead provide
  `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_SESSION_TOKEN`
  as environment variables.

This project uses the Glue-registered Silver tables in
`fdp_dev_batch_lakehouse` as sources and builds dbt-managed staging,
intermediate, mart, and reporting models in Athena-managed schemas.

For realtime analytics, the same project also supports a separate `streaming`
target that reads from `fdp_dev_streaming_lakehouse` and writes isolated
streaming analytics models into `fdp_dev_streaming_analytics`.
