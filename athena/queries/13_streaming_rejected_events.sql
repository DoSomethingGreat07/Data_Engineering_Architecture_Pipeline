-- Run in Amazon Athena
SELECT
  processing_date,
  rejection_reason,
  COUNT(*) AS rejected_event_count
FROM fdp_dev_streaming_lakehouse.rejected_stream_events
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

