"""
Audio Processor
===============

Handles real-time audio pipeline:
- Accepts inbound audio (Twilio WebSocket)
- Streams to Deepgram STT for transcription
- Receives final transcript chunks
- Sends responses to TTS (ElevenLabs)
- Returns synthesized audio stream to Twilio
- Handles noise reduction, silence detection, and language selection
"""

import asyncio
import aiohttp
import logging
import numpy as np
import soundfile as sf
from typing import AsyncGenerator, Dict, Optional

from ..services.stt_service import STTService
from ..services.tts_service import TTSService
from ..orchestration.state_manager import StateManager
from ..core.config import settings
from ..voice.interrupt_handler import InterruptHandler

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, session_id: str, language: str = "en"):
        self.session_id = session_id
        self.language = language
        self.state_manager = StateManager()
        self.interrupt_handler = InterruptHandler(session_id=session_id)
        self.stt_service = STTService(language=language)
        self.tts_service = TTSService(language=language)
        self._is_running = True
        self._input_queue: asyncio.Queue = asyncio.Queue()

    # ------------------------------------------------------------
    # AUDIO INGESTION
    # ------------------------------------------------------------
    async def receive_audio_chunk(self, chunk: bytes):
        """
        Receive raw PCM audio bytes from Twilio stream.
        Adds chunk to internal buffer queue.
        """
        if not self._is_running:
            return
        await self._input_queue.put(chunk)

    # ------------------------------------------------------------
    # AUDIO PROCESSING LOOP
    # ------------------------------------------------------------
    async def process_audio(self) -> AsyncGenerator[Dict, None]:
        """
        Core async pipeline that:
        1. Reads chunks from queue
        2. Streams them to STT
        3. Yields interim/final transcription results
        """
        async for transcript in self.stt_service.stream_transcribe(self._audio_generator()):
            if transcript.get("is_final"):
                logger.debug(f"[{self.session_id}] Final transcript: {transcript['text']}")
                yield transcript
            else:
                # For live feedback or interruption
                await self.interrupt_handler.check_user_interrupt(transcript.get("text"))

    async def _audio_generator(self):
        """Async generator feeding queued chunks to STT service."""
        while self._is_running:
            chunk = await self._input_queue.get()
            if chunk is None:
                break
            yield chunk

    # ------------------------------------------------------------
    # TTS SYNTHESIS
    # ------------------------------------------------------------
    async def synthesize_response(self, text: str) -> bytes:
        """
        Convert agent text reply to speech audio using ElevenLabs.
        """
        if not text:
            return b""
        return await self.tts_service.text_to_speech(text)

    # ------------------------------------------------------------
    # AUDIO UTILITIES
    # ------------------------------------------------------------
    @staticmethod
    def normalize_audio(data: np.ndarray) -> np.ndarray:
        """Normalize audio amplitude."""
        peak = np.max(np.abs(data))
        return data / peak if peak > 0 else data

    @staticmethod
    def remove_silence(data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Remove low-amplitude regions."""
        return data[np.abs(data) > threshold]

    # ------------------------------------------------------------
    # SESSION CONTROL
    # ------------------------------------------------------------
    async def close(self):
        """Gracefully close session."""
        self._is_running = False
        await self._input_queue.put(None)
        await self.state_manager.delete_session(self.session_id)
        logger.info(f"AudioProcessor closed for session {self.session_id}")
