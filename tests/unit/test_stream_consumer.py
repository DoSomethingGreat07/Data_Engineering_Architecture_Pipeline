import json
from pathlib import Path

from src.stream_consumer.service import ConsumeRequest, KinesisStreamConsumerService


class FakeKinesisClient:
    def list_shards(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        return {"Shards": [{"ShardId": "shardId-000"}]}

    def get_shard_iterator(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        return {"ShardIterator": "iterator-1"}

    def get_records(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        return {
            "Records": [
                {
                    "PartitionKey": "SEC-AAPL",
                    "SequenceNumber": "1",
                    "Data": json.dumps(
                        {
                            "event_id": "EVT-1",
                            "event_type": "trade",
                            "partition_key": "SEC-AAPL",
                            "trade_id": "ALPACA-AAPL-1",
                            "account_id": "ACCT-1",
                            "customer_id": "CUST-1",
                            "security_id": "SEC-AAPL",
                            "transaction_amount": "100.25",
                            "currency_code": "USD",
                            "transaction_status": "POSTED",
                            "event_timestamp": "2026-08-17T00:00:00Z",
                            "processing_timestamp": "2026-08-17T00:00:01Z",
                            "country_code": "US",
                            "risk_score": 30,
                            "quantity": "10",
                            "price": "10.025",
                            "side": "BUY",
                        }
                    ).encode("utf-8"),
                }
            ],
            "NextShardIterator": None,
        }


def test_consume_to_directory_writes_expected_files(tmp_path: Path) -> None:
    service = KinesisStreamConsumerService(FakeKinesisClient())

    result = service.consume_to_directory(
        output_dir=tmp_path / "external",
        bronze_root=tmp_path / "lakehouse" / "raw",
        request=ConsumeRequest(stream_name="fdp-dev-events", max_records=10),
    )

    assert result.records_read == 1
    assert result.parsed_records == 1
    assert result.parse_failures == 0
    assert result.paths.raw_messages_path.exists()
    assert result.paths.canonical_events_path.exists()
    assert result.paths.bronze_events_path.exists()
    assert "EVT-1" in result.paths.canonical_events_path.read_text(encoding="utf-8")
