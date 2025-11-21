import pytest
from app.services.payment_service import PaymentService

def test_create_payment_intent_mocked(monkeypatch):
    """Mock Stripe PaymentIntent to test PaymentService logic."""
    class FakePI:
        id = "pi_123"

    def fake_create(**kwargs):
        return FakePI()

    # Patch Stripe's real create() call
    monkeypatch.setattr("stripe.PaymentIntent.create", fake_create)

    # Run the service method
    res = PaymentService.create_payment_intent(1000, "inr", idempotency_key="key123")

    # Validate result
    assert res["success"] is True
    assert "payment_intent" in res
    assert res["payment_intent"]["id"] == "pi_123"
