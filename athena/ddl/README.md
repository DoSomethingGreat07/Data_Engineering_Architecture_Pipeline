# Athena DDL Notes

Run these scripts in Amazon Athena.

Official support note:
- Athena can query Delta Lake tables directly when the tables are registered in AWS Glue.
- The DDL for Delta tables should use only `LOCATION` and `TBLPROPERTIES ('table_type'='DELTA')`.

Reference:
- AWS Athena documentation for Delta Lake table support and getting started.

