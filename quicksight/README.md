# QuickSight Phase 14

This directory contains Amazon QuickSight handoff assets, dashboard specifications, and connection guidance for the Athena/Glue reporting layer.

Run locations:
- Dashboard spec: documentation only
- Generated batch handoff package in `output/`: produced by `src.quicksight_handoff.cli`
- Generated streaming handoff package in `streaming_output/`: produced by `src.quicksight_handoff.cli --mode streaming`

QuickSight is not provisioned directly from this repository. Instead, this phase provides:
- Athena dataset definitions and connection guidance
- dashboard blueprint for QuickSight analyses
- setup steps for Athena, Glue, and S3 permissions
- generated handoff artifacts after successful batch and streaming pipeline runs
