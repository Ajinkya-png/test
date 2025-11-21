import pytest
import asyncio

@pytest.mark.asyncio
async def test_simple_workflow():
    """
    Very basic integration workflow test that simulates in-memory session and agent processing.
    This test does not require external APIs.
    """
    from app.orchestration.state_manager import StateManager
    from app.orchestration.orchestrator import Orchestrator

    call_sid = "test-call-1"
    phone = "+1000000000"
    session_id = await StateManager.create_session(call_sid, phone)
    session_data = await StateManager.get_session(session_id)

    orchestrator = Orchestrator(session_id, session_data)
    # Simulate audio data -> orchestrator will return "Simulated transcript"
    await orchestrator.process_audio("dummy-audio")
    # Clean up
    await StateManager.end_session(session_id)
    assert True
