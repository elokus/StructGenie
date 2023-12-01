from __future__ import annotations

import logging
from structgenie.utils.logging import console_logger as logger
from importlib.metadata import version
from typing import Callable, Any, Type, List

from packaging.version import parse
from tenacity import before_sleep_log, RetryCallState, retry_if_exception_type, retry, stop_after_attempt, \
    wait_exponential

from structgenie.base import BaseGenerationDriver


def is_openai_v1() -> bool:
    _version = parse(version("openai"))
    return _version.major >= 1


def _create_retry_decorator(
    driver: BaseGenerationDriver,
) -> Callable[[Any], Any]:
    import openai

    errors = [
        openai.Timeout,
        openai.APIError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.RateLimitError,
        openai.InternalServerError,
    ]
    return create_base_retry_decorator(
        error_types=errors, max_retries=driver.max_retries
    )


def create_base_retry_decorator(
    error_types: List[Type[BaseException]],
    max_retries: int = 1,
) -> Callable[[Any], Any]:
    """Create a retry decorator for a given LLM and provided list of error types."""

    _logging = before_sleep_log(logger, logging.WARNING)

    def _before_sleep(retry_state: RetryCallState) -> None:
        _logging(retry_state)

    min_seconds = 4
    max_seconds = 10
    # Wait 2^x * 1 second between each retry starting with
    # 4 seconds, then up to 10 seconds, then 10 seconds afterwards
    retry_instance: "retry_base" = retry_if_exception_type(error_types[0])
    for error in error_types[1:]:
        retry_instance = retry_instance | retry_if_exception_type(error)
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=min_seconds, max=max_seconds),
        retry=retry_instance,
        before_sleep=_before_sleep,
    )