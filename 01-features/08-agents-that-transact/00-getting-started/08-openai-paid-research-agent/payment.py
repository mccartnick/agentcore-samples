"""Small, framework-agnostic AgentCore x402 payment exercise."""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx


class ResponseLike(Protocol):
    """The response attributes used by the payment flow."""

    status_code: int
    headers: Mapping[str, str]
    text: str


class PaymentManagerLike(Protocol):
    """Subset of PaymentManager used by this tutorial."""

    def create_payment_session(self, **kwargs: Any) -> dict[str, Any]: ...

    def generate_payment_header(self, **kwargs: Any) -> dict[str, str]: ...


HttpGet = Callable[..., ResponseLike]


@dataclass(frozen=True)
class PaymentConfig:
    """Configuration shared by session creation and the paid fetch."""

    manager_arn: str
    instrument_id: str
    user_id: str
    region: str
    paid_url: str
    budget: str
    expiry_minutes: int

    @classmethod
    def from_env(cls) -> PaymentConfig:
        """Load Tutorial 00 resources plus this tutorial's local overrides."""
        values = {
            "manager_arn": os.getenv("PAYMENT_MANAGER_ARN", "").strip(),
            "instrument_id": os.getenv("INSTRUMENT_ID", "").strip(),
            "user_id": os.getenv("USER_ID", "").strip(),
            "paid_url": os.getenv("PAID_RESEARCH_URL", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        parsed_url = urlparse(values["paid_url"])
        if parsed_url.scheme != "https" or not parsed_url.hostname:
            raise ValueError("PAID_RESEARCH_URL must be an absolute HTTPS URL")

        expiry_minutes = int(os.getenv("PAYMENT_SESSION_EXPIRY_MINUTES", "60"))
        if expiry_minutes < 15 or expiry_minutes > 480:
            raise ValueError("PAYMENT_SESSION_EXPIRY_MINUTES must be between 15 and 480")

        return cls(
            **values,
            region=os.getenv("AWS_REGION", "us-east-1"),
            budget=os.getenv("PAID_RESEARCH_BUDGET", "0.25"),
            expiry_minutes=expiry_minutes,
        )


def create_payment_session(
    manager: PaymentManagerLike,
    config: PaymentConfig,
    *,
    token_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
) -> str:
    """Create one budget-bounded session and return its ID.

    TODO:
    1. Call ``manager.create_payment_session``.
    2. Scope it to ``config.user_id``.
    3. Apply ``config.budget`` as ``maxSpendAmount`` in USD.
    4. Apply ``config.expiry_minutes`` and an idempotency token.
    5. Return ``paymentSessionId``.
    """
    raise NotImplementedError("Implement create_payment_session in payment.py")


def fetch_x402(
    manager: PaymentManagerLike,
    config: PaymentConfig,
    payment_session_id: str,
    *,
    http_get: HttpGet = httpx.get,
    token_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
) -> str:
    """Fetch the approved URL, settle one 402 challenge, and return JSON.

    TODO:
    1. GET ``config.paid_url`` without following redirects.
    2. If it is not a 402, return a JSON object with the status, body, and
       ``payment_made`` set to false.
    3. Pass the complete 402 response to
       ``manager.generate_payment_header`` with the instrument, session, user,
       and one idempotency token.
    4. Retry the same URL with the generated header.
    5. Return a JSON object with the retry status, body, and payment outcome.

    Keep the URL application-bound: this function intentionally accepts no URL
    argument.
    """
    raise NotImplementedError("Implement fetch_x402 in payment.py")
