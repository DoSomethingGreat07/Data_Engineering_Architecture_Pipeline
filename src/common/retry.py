from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from botocore.exceptions import ClientError, ConnectionError, EndpointConnectionError

LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


def is_retryable_aws_error(error: Exception) -> bool:
    if isinstance(error, ConnectionError | EndpointConnectionError | TimeoutError):
        return True
    if isinstance(error, ClientError):
        error_code = error.response.get("Error", {}).get("Code", "")
        return error_code in {
            "RequestTimeout",
            "Throttling",
            "ThrottlingException",
            "InternalError",
            "SlowDown",
            "ServiceUnavailable",
        }
    return False


def retry(operation: Callable[[], T], retries: int = 3, delay_seconds: float = 1.0) -> T:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return operation()
        except Exception as error:  # noqa: BLE001
            last_error = error
            if not is_retryable_aws_error(error) or attempt == retries:
                raise
            LOGGER.warning(
                "retrying operation after retryable error",
                extra={"attempt": attempt, "retries": retries, "error": str(error)},
            )
            time.sleep(delay_seconds * attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry failed without capturing an error")
