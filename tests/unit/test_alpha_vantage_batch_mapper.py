from pathlib import Path

from src.sources.alpha_vantage_batch.client import AlphaVantageBatchClient
from src.sources.alpha_vantage_batch.mapper import (
    map_alpha_vantage_bundle,
    map_daily_prices,
    map_security_overview,
    normalize_security_type,
)
from src.sources.alpha_vantage_batch.models import AlphaVantageConfig, AlphaVantageRawBundle
from src.sources.alpha_vantage_batch.service import AlphaVantageBatchExtractionService


def build_raw_bundle() -> AlphaVantageRawBundle:
    csv_text = (
        "symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        "AAPL,Apple Inc,NASDAQ,Stock,1980-12-12,,Active\n"
        "VOO,Vanguard S&P 500 ETF,NYSE ARCA,ETF,2010-09-07,,Active\n"
    )
    return AlphaVantageRawBundle(
        request_params={"function": "LISTING_STATUS", "state": "active"},
        listings_csv=csv_text,
        listings=[
            {
                "symbol": "AAPL",
                "name": "Apple Inc",
                "exchange": "NASDAQ",
                "assetType": "Stock",
                "ipoDate": "1980-12-12",
                "delistingDate": "",
                "status": "Active",
            },
            {
                "symbol": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "exchange": "NYSE ARCA",
                "assetType": "ETF",
                "ipoDate": "2010-09-07",
                "delistingDate": "",
                "status": "Active",
            },
        ],
        overviews={
            "AAPL": {
                "Symbol": "AAPL",
                "Name": "Apple Inc",
                "Exchange": "NASDAQ",
                "Currency": "USD",
                "Country": "US",
                "Sector": "Technology",
                "Industry": "Consumer Electronics",
                "MarketCapitalization": "3000000000000",
                "PERatio": "31.5",
                "DividendYield": "0.0045",
                "Beta": "1.21",
                "FiscalYearEnd": "September",
                "LatestQuarter": "2026-06-30",
            }
        },
        daily_time_series={
            "AAPL": {
                "Meta Data": {"2. Symbol": "AAPL"},
                "Time Series (Daily)": {
                    "2026-08-14": {
                        "1. open": "223.10",
                        "2. high": "225.40",
                        "3. low": "221.50",
                        "4. close": "224.75",
                        "5. volume": "53440000",
                    },
                    "2026-08-13": {
                        "1. open": "220.00",
                        "2. high": "223.50",
                        "3. low": "219.80",
                        "4. close": "222.90",
                        "5. volume": "44100000",
                    },
                },
            }
        },
    )


def test_map_alpha_vantage_bundle_creates_security_records() -> None:
    bundle = map_alpha_vantage_bundle(build_raw_bundle())
    assert bundle.securities[0]["security_id"] == "SEC-AAPL"
    assert bundle.securities[0]["security_type"] == "EQUITY"
    assert bundle.securities[1]["security_type"] == "ETF"
    assert bundle.security_overviews[0]["sector"] == "Technology"
    assert bundle.daily_prices[0]["security_id"] == "SEC-AAPL"
    assert bundle.metadata["source_system"] == "alpha_vantage"


def test_normalize_security_type_handles_blank_and_stock() -> None:
    assert normalize_security_type(None) == "EQUITY"
    assert normalize_security_type("Stock") == "EQUITY"
    assert normalize_security_type("mutual fund") == "MUTUAL_FUND"


def test_client_parses_listing_csv() -> None:
    csv_text = (
        "symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        "AAPL,Apple Inc,NASDAQ,Stock,1980-12-12,,Active\n"
    )
    rows = AlphaVantageBatchClient._parse_csv(csv_text)
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["assetType"] == "Stock"


def test_map_security_overview_builds_enrichment_record() -> None:
    overview = map_security_overview(
        "AAPL",
        {
            "Name": "Apple Inc",
            "Exchange": "NASDAQ",
            "Currency": "USD",
            "Country": "US",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "MarketCapitalization": "1000",
        },
    )
    assert overview["security_id"] == "SEC-AAPL"
    assert overview["market_cap"] == "1000"


def test_map_daily_prices_flattens_time_series() -> None:
    records = map_daily_prices(
        "AAPL",
        {
            "Time Series (Daily)": {
                "2026-08-15": {
                    "1. open": "10",
                    "2. high": "11",
                    "3. low": "9",
                    "4. close": "10.5",
                    "5. volume": "1000",
                }
            }
        },
    )
    assert records[0]["security_id"] == "SEC-AAPL"
    assert records[0]["close_price"] == "10.5"


def test_write_bundle_creates_output_files(tmp_path: Path) -> None:
    service = AlphaVantageBatchExtractionService(
        client=AlphaVantageBatchClient(AlphaVantageConfig(api_key="demo"))
    )
    paths = service.write_bundle(
        output_dir=tmp_path,
        raw_bundle=build_raw_bundle(),
        normalized_bundle=map_alpha_vantage_bundle(build_raw_bundle()),
    )
    assert paths.raw_listings_path.exists()
    assert paths.canonical_securities_path.exists()
    assert paths.raw_overviews_path.exists()
    assert paths.canonical_daily_prices_path.exists()
