from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from ironman.api.main import app


client = TestClient(app)


def test_event_api_rejects_non_utc_event() -> None:
    response = client.post(
        "/api/v1/ledger/events",
        json={
            "event_type": "CASH_DEPOSIT",
            "effective_at": "2026-01-01T12:00:00",
            "financial_date": "2026-01-01",
            "timezone": "Asia/Kolkata",
            "source": "manual",
            "legs": [{"leg_type": "CASH", "direction": "IN", "account_id": str(uuid4()), "currency": "INR", "amount": "10"}],
        },
    )
    assert response.status_code == 422
