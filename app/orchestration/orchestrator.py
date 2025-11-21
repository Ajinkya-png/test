
# app/orchestration/orchestrator.py
import base64
import io
import wave
import audioop
import logging
import asyncio
from typing import Dict, Any, Optional

from ..services.stt_service import STTService
from ..services.tts_service import TTSService
from ..services.llm_service import LLMService
from .state_manager import StateManager
from ..core.config import settings

logger = logging.getLogger(__name__)

# In-memory audio store (demo). Prefer Redis for production.
_AUDIO_STORE: Dict[str, bytes] = {}


def ulaw_to_wav_bytes(ulaw_bytes: bytes, channels=1, sample_rate=8000) -> bytes:
    """
    Convert μ-law PCM bytes (8-bit) to 16-bit PCM WAV bytes.
    """
    try:
        pcm16 = audioop.ulaw2lin(ulaw_bytes, 2)  # 16-bit output
        buf = io.BytesIO()
        wf = wave.open(buf, "wb")
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16)
        wf.close()
        return buf.getvalue()
    except Exception as e:
        logger.exception("Error converting ulaw->wav: %s", e)
        return b""


class Orchestrator:
    def __init__(self, session_id: str, session_data: Dict[str, Any]):
        self.session_id = session_id
        self.session_data = session_data or {}
        self.stt = STTService()
        self.tts = TTSService()
        self.llm = LLMService()

    async def process_audio(self, media_payload_b64: str) -> Optional[bytes]:
        """
            Receives Twilio media payload (base64 of PCM16LE samples).
            1. Decode base64 -> PCM bytes
            2. Wrap PCM in WAV and call STT (Deepgram)
            3. Use NLU or orchestration to produce a reply_text (synchronously or async)
            4. Call TTS to produce μ-law raw bytes
            5. Return μ-law bytes (raw) to the caller, which will base64-encode before sending back to Twilio
            """
        try:
            # 1. DECODE
            pcm_bytes = base64.b64decode(media_payload_b64)

            # debug
            logger.info(f"[process_audio] Received PCM bytes: {len(pcm_bytes)}")

            # 2. Create WAV bytes for STT
            from .utils_audio import pcm16le_bytes_to_wav_bytes  # import helper
            wav_bytes = pcm16le_bytes_to_wav_bytes(pcm_bytes, sample_rate=8000)

            # 3. STT
            # Blocking network call -> use thread to avoid blocking loop
            loop = __import__("asyncio").get_running_loop()
            transcript = await loop.run_in_executor(None, self.stt.transcribe_bytes, wav_bytes, "audio/wav")
            logger.info(f"[process_audio] Transcript: {transcript}")

            if not transcript:
                logger.info("[process_audio] No transcript returned, skipping reply.")
                return None

            # 4. Decide reply_text (very simple example — replace with your NLU)
            reply_text = self.decide_reply(transcript)  # implement your decision logic
            if not reply_text:
                logger.info("[process_audio] NLU returned no reply.")
                return None

            # 5. TTS (blocking -> thread)
            reply_audio_bytes = await loop.run_in_executor(None, self.tts.synthesize, reply_text)
            if not reply_audio_bytes:
                logger.error("[process_audio] TTS returned None.")
                return None

            # reply_audio_bytes MUST be raw μ-law bytes here (per updated TTS)
            return reply_audio_bytes

        except Exception as e:
            logger.exception(f"[process_audio] Unexpected error: {e}")
            return None
        
    # Add to your Orchestrator class
    async def process_text(self, text: str) -> bytes:
        """Convert text to audio for initial greetings"""
        try:
            from ..services.tts_service import TTSService
            tts_service = TTSService()
            return await tts_service.text_to_speech(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""