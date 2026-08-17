from src.common.config import load_settings


def test_load_settings_reads_test_config() -> None:
    settings = load_settings("config/test.yaml")
    assert settings.app.env == "test"
    assert settings.generation.seed == 4242
    assert settings.generation.accounts_per_customer.max == 2

