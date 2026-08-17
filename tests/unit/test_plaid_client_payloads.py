from src.sources.plaid_batch.client import PlaidBatchClient, default_sandbox_transactions
from src.sources.plaid_batch.models import PlaidConfig


class RecordingPlaidClient(PlaidBatchClient):
    def __init__(self, config: PlaidConfig) -> None:
        super().__init__(config)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def _post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((path, payload))
        if path == "/institutions/search":
            return {
                "institutions": [
                    {
                        "institution_id": "ins_123",
                        "name": "Navy Federal Credit Union",
                    }
                ]
            }
        if path == "/sandbox/transactions/create":
            return {"request_id": "req-seeded"}
        return {
            "link_token": "link-sandbox-123",
            "expiration": "2026-08-15T23:59:59Z",
            "request_id": "req-123",
        }


def test_create_link_token_uses_customer_context() -> None:
    client = RecordingPlaidClient(PlaidConfig(client_id="id", secret="secret"))
    response = client.create_link_token(
        user_id="CUST-1",
        full_name="Member One",
        email="member@example.com",
    )
    path, payload = client.calls[0]
    assert path == "/link/token/create"
    assert payload["user"]["client_user_id"] == "CUST-1"
    assert response["link_token"] == "link-sandbox-123"


def test_search_institutions_returns_model_results() -> None:
    client = RecordingPlaidClient(PlaidConfig(client_id="id", secret="secret"))
    results = client.search_institutions("Navy Federal Credit Union")
    assert results[0].institution_id == "ins_123"
    assert results[0].name == "Navy Federal Credit Union"


def test_create_sandbox_public_token_supports_dynamic_user() -> None:
    client = RecordingPlaidClient(PlaidConfig(client_id="id", secret="secret"))
    client.create_sandbox_public_token(override_username="user_transactions_dynamic")
    path, payload = client.calls[0]
    assert path == "/sandbox/public_token/create"
    assert payload["options"]["override_username"] == "user_transactions_dynamic"


def test_default_sandbox_transactions_are_recent() -> None:
    transactions = default_sandbox_transactions()
    assert len(transactions) == 10
    assert transactions[0].description == "NAVY FEDERAL PAYROLL"


def test_default_sandbox_transactions_vary_by_seed() -> None:
    first = default_sandbox_transactions(seed="run-1")
    second = default_sandbox_transactions(seed="run-2")
    assert [item.amount for item in first] != [item.amount for item in second]
    assert [item.description for item in first] == [item.description for item in second]
