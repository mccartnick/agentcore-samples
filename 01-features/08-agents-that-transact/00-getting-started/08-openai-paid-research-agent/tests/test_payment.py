from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from payment import PaymentConfig, create_payment_session, fetch_x402


@dataclass
class FakeResponse:
    status_code: int
    text: str
    headers: dict[str, str] = field(default_factory=dict)


class FakeManager:
    def __init__(self) -> None:
        self.session_calls: list[dict[str, Any]] = []
        self.header_calls: list[dict[str, Any]] = []

    def create_payment_session(self, **kwargs: Any) -> dict[str, str]:
        self.session_calls.append(kwargs)
        return {"paymentSessionId": "session-123"}

    def generate_payment_header(self, **kwargs: Any) -> dict[str, str]:
        self.header_calls.append(kwargs)
        return {"PAYMENT-SIGNATURE": "proof"}


def config() -> PaymentConfig:
    return PaymentConfig(
        manager_arn="arn:manager",
        instrument_id="instrument-123",
        user_id="student",
        region="us-east-1",
        paid_url="https://merchant.example/research",
        budget="0.25",
        expiry_minutes=60,
    )


def test_creates_a_budget_bounded_session() -> None:
    manager = FakeManager()

    session_id = create_payment_session(
        manager,
        config(),
        token_factory=lambda: "session-token",
    )

    assert session_id == "session-123"
    assert manager.session_calls == [
        {
            "user_id": "student",
            "limits": {"maxSpendAmount": {"value": "0.25", "currency": "USD"}},
            "expiry_time_in_minutes": 60,
            "client_token": "session-token",
        }
    ]


def test_settles_one_402_and_retries_the_same_url() -> None:
    responses = iter(
        [
            FakeResponse(402, '{"x402Version": 2}', {"payment-required": "challenge"}),
            FakeResponse(200, '{"premium": "evidence"}'),
        ]
    )
    requests: list[dict[str, Any]] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        requests.append({"url": url, **kwargs})
        return next(responses)

    manager = FakeManager()
    result = json.loads(
        fetch_x402(
            manager,
            config(),
            "session-123",
            http_get=fake_get,
            token_factory=lambda: "payment-token",
        )
    )

    assert result["status_code"] == 200
    assert result["payment_made"] is True
    assert requests[0]["url"] == requests[1]["url"] == config().paid_url
    assert requests[1]["headers"] == {"PAYMENT-SIGNATURE": "proof"}
    assert manager.header_calls[0]["client_token"] == "payment-token"


def test_returns_free_content_without_generating_a_payment() -> None:
    manager = FakeManager()

    result = json.loads(
        fetch_x402(
            manager,
            config(),
            "session-123",
            http_get=lambda *_args, **_kwargs: FakeResponse(200, "public response"),
        )
    )

    assert result["status_code"] == 200
    assert result["payment_made"] is False
    assert manager.header_calls == []
