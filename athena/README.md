# Athena Phase 6

This directory contains Athena DDL and analytical queries for the financial data platform.

Current implementation choices:

- Primary lakehouse format remains Delta Lake.
- Athena reads Delta Lake tables through AWS Glue registrations when supported.
- If direct querying becomes unreliable for your environment, publish an Athena-friendly Gold layer in Parquet without changing the primary Delta architecture.

Run Athena SQL in Amazon Athena, using the database created in AWS Glue and the workgroup approved for your environment.

