"""
Tests core services:
- LLMService (mocked Anthropic/OpenAI)
- STTService (mocked Deepgram)
- TTSService (mocked ElevenLabs)
- PaymentService (mocked Stripe)
- CRMService (mocked HubSpot)
"""

import pytest
from unittest.mock import patch
from app.services.llm_service import LLMService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.payment_service import PaymentService
from app.services.crm_service import CRMService

@pytest.fixture
def dummy_text():
    return "Hello, this is a test."

@patch("app.services.llm_service.openai.ChatCompletion.create")
def test_llm_service_openai(mock_create, dummy_text):
    mock_create.return_value = {"choices": [{"message": {"content": "Hi there!"}}]}
    llm = LLMService(provider="openai")
    result = llm.generate_response(dummy_text)
    assert "Hi there" in result

def test_stt_service_transcription(monkeypatch):
    monkeypatch.setattr("app.services.stt_service.DeepgramClient.transcribe", lambda *a, **k: {"results": "Transcribed text"})
    stt = STTService()
    res = stt.transcribe_audio(b"fake_audio_data")
    assert "Transcribed" in res["results"]

def test_tts_service_generation(monkeypatch):
    monkeypatch.setattr("app.services.tts_service.ElevenLabsClient.generate", lambda *a, **k: b"FAKEAUDIO")
    tts = TTSService()
    audio = tts.synthesize_text("Hello", voice="Rachel")
    assert isinstance(audio, bytes)
    assert audio.startswith(b"FAKE")

def test_payment_service_create_intent(monkeypatch):
    class FakePI: id = "pi_123"
    monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: FakePI())
    res = PaymentService.create_payment_intent(1000, "inr")
    assert res["success"]
    assert "pi_" in res["payment_intent"].id

def test_crm_service_upsert(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *a, **k: type("R", (), {"ok": True, "json": lambda s: {"id": "12345"}})())
    crm = CRMService()
    res = crm.upsert_customer({"name": "Ajinkya", "email": "aj@example.com", "phone_number": "9876543210"})
    assert res["success"]
    assert res["crm_id"] == "12345"
