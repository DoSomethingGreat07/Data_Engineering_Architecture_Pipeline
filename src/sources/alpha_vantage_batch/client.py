from __future__ import annotations

import csv
from io import StringIO
from typing import Any

import requests

from src.sources.alpha_vantage_batch.models import AlphaVantageConfig


class AlphaVantageBatchClient:
    def __init__(self, config: AlphaVantageConfig) -> None:
        self.config = config

    def get_listing_status(
        self,
        *,
        date: str | None = None,
        state: str | None = None,
    ) -> tuple[str, list[dict[str, str]], dict[str, Any]]:
        params: dict[str, Any] = {
            "function": "LISTING_STATUS",
            "apikey": self.config.api_key,
        }
        if date:
            params["date"] = date
        if state or self.config.default_state:
            params["state"] = state or self.config.default_state

        csv_text = self._get_text_response(params)
        if "Error Message" in csv_text or "Information" in csv_text:
            raise ValueError(f"Alpha Vantage returned a non-CSV response: {csv_text[:200]}")
        return csv_text, self._parse_csv(csv_text), params

    def get_company_overview(self, symbol: str) -> dict[str, Any]:
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.config.api_key,
        }
        return self._get_json_response(params)

    def get_daily_time_series(
        self,
        symbol: str,
        *,
        outputsize: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize or self.config.default_daily_outputsize,
            "apikey": self.config.api_key,
        }
        return self._get_json_response(params)

    @staticmethod
    def _parse_csv(csv_text: str) -> list[dict[str, str]]:
        reader = csv.DictReader(StringIO(csv_text))
        return [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]

    def _get_text_response(self, params: dict[str, Any]) -> str:
        response = requests.get(
            self.config.base_url,
            params=params,
            timeout=60,
            headers={"User-Agent": "production-pipeline/1.0"},
        )
        response.raise_for_status()
        return response.text

    def _get_json_response(self, params: dict[str, Any]) -> dict[str, Any]:
        response = requests.get(
            self.config.base_url,
            params=params,
            timeout=60,
            headers={"User-Agent": "production-pipeline/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Alpha Vantage JSON response must be an object")
        if "Error Message" in payload or "Information" in payload:
            raise ValueError(f"Alpha Vantage returned an error payload: {payload}")
        return payload
