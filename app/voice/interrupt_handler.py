"""
Interrupt Handler
=================

Detects and manages barge-in (user speaking over agent).

Features:
- VAD-based detection of user speech while TTS is active
- Stops current TTS playback
- Cancels queued responses
- Signals orchestrator to resume listening mode
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from ..orchestration.state_manager import StateManager

logger = logging.getLogger(__name__)

class InterruptHandler:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_manager = StateManager()
        self.last_interrupt_time: Optional[datetime] = None
        self.tts_playing = False
        self.lock = asyncio.Lock()

    # ------------------------------------------------------------
    # USER INTERRUPTION DETECTION
    # ------------------------------------------------------------
    async def check_user_interrupt(self, transcript: Optional[str]) -> bool:
        """
        Called continuously during STT streaming.
        Detects user speech while TTS is active.
        """
        if not transcript:
            return False
        async with self.lock:
            if self.tts_playing and len(transcript.strip()) > 1:
                now = datetime.utcnow()
                if not self.last_interrupt_time or now - self.last_interrupt_time > timedelta(milliseconds=200):
                    await self.handle_interrupt()
                    self.last_interrupt_time = now
                    return True
        return False

    # ------------------------------------------------------------
    # HANDLE INTERRUPTION
    # ------------------------------------------------------------
    async def handle_interrupt(self):
        """Stop ongoing TTS and resume STT listening."""
        logger.info(f"[{self.session_id}] User interrupted — stopping TTS output.")
        await self.state_manager.set(self.session_id, "tts_active", False)
        await self.state_manager.set(self.session_id, "mode", "listening")

    async def mark_tts_active(self, active: bool = True):
        """Track whether TTS playback is currently active."""
        async with self.lock:
            self.tts_playing = active
            await self.state_manager.set(self.session_id, "tts_active", active)
