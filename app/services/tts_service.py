# import asyncio
# import io
# import logging
# from typing import Optional, AsyncGenerator
# import elevenlabs
# from elevenlabs import Voice, VoiceSettings
# from ..core.config import settings

# logger = logging.getLogger(__name__)


# class TTSService:
#     """
#     Wrapper for ElevenLabs TTS generation. Supports streaming generation (if supported by SDK)
#     and full audio generation to bytes (for saving to file).
#     """
#     def __init__(self):
#         elevenlabs.set_api_key(settings.ELEVENLABS_API_KEY)
#         # Predefine voices/settings — these voice IDs are placeholders; replace with valid IDs for your ElevenLabs account.
#         self.voices = {
#             "customer_agent": Voice(
#                 voice_id="EXAVITQu4vr4xnSDxMaL",  # Rachel - friendly, clear (example)
#                 settings=VoiceSettings(
#                     stability=0.3,
#                     similarity_boost=0.7,
#                     style=0.5,
#                     use_speaker_boost=True
#                 )
#             ),
#             "support_agent": Voice(
#                 voice_id="VR6AewLTigWG4xSOukaG",  # Arnold - professional, calm (example)
#                 settings=VoiceSettings(
#                     stability=0.4,
#                     similarity_boost=0.75,
#                     style=0.3,
#                     use_speaker_boost=True
#                 )
#             )
#         }

#     async def generate_speech(
#         self,
#         text: str,
#         voice_type: str = "customer_agent",
#         stream: bool = False
#     ) -> AsyncGenerator[bytes, None]:
#         """
#         Generate speech from text.
#         - If stream=True, yields audio chunks (async), otherwise yields a single bytes object containing full audio.
#         Note: exact streaming API depends on elevenlabs SDK version; this implementation uses the higher-level
#         generate method and yields chunks if streaming is supported.
#         """
#         try:
#             voice = self.voices.get(voice_type, self.voices["customer_agent"])

#             if stream:
#                 # If SDK supports streaming, iterate through the stream
#                 audio_stream = elevenlabs.generate(
#                     text=text,
#                     voice=voice,
#                     model="eleven_monolingual_v1",
#                     stream=True
#                 )

#                 # elevenlabs.generate(..., stream=True) may be synchronous iterator or async; adapt below.
#                 # We'll attempt to iterate it in an async-friendly way.
#                 if hasattr(audio_stream, "__aiter__"):
#                     async for chunk in audio_stream:
#                         yield chunk
#                 else:
#                     for chunk in audio_stream:
#                         yield chunk
#             else:
#                 # Generate complete audio (bytes)
#                 audio = elevenlabs.generate(
#                     text=text,
#                     voice=voice,
#                     model="eleven_monolingual_v1"
#                 )
#                 yield audio

#         except Exception as e:
#             logger.error(f"TTS generation error: {e}")
#             # Fallback to a simple error message audio (best-effort)
#             fallback_text = "I apologize, but I'm having trouble speaking right now."
#             try:
#                 audio = elevenlabs.generate(
#                     text=fallback_text,
#                     voice=self.voices["customer_agent"],
#                     model="eleven_monolingual_v1"
#                 )
#                 yield audio
#             except Exception:
#                 # Ultimate fallback - return empty bytes
#                 yield b""

#     async def text_to_speech_file(self, text: str, output_path: str, voice_type: str = "customer_agent") -> bool:
#         """Generate speech and save to a file path (blocking write)"""
#         try:
#             audio = elevenlabs.generate(
#                 text=text,
#                 voice=self.voices.get(voice_type, self.voices["customer_agent"]),
#                 model="eleven_monolingual_v1"
#             )

#             with open(output_path, 'wb') as f:
#                 f.write(audio)

#             return True
#         except Exception as e:
#             logger.error(f"TTS file generation error: {e}")
#             return False

# app/services/tts_service.py
# import logging
# import requests
# from typing import Iterator, Optional
# from io import BytesIO

# logger = logging.getLogger(__name__)

# class TTSService:
#     """
#     Synthesize text to speech using ElevenLabs HTTP API (sync).
#     Returns raw audio bytes (mp3) that can be served to Twilio via an HTTP GET.
#     """
#     def __init__(self, api_key: str = None):
#         from ..core.config import settings
#         self.api_key = api_key or settings.ELEVENLABS_API_KEY
#         # default voice id environment variables in your .env (ELEVENLABS_VOICE_EN)
#         self.default_voice = getattr(__import__("os"), "environ").get("ELEVENLABS_VOICE_EN", None)

#     def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
#         if not self.api_key:
#             logger.warning("ElevenLabs API key not set; TTS disabled.")
#             return None

#         voice_id = voice or self.default_voice
#         if not voice_id:
#             logger.warning("No ElevenLabs voice specified.")
#             return None

#         url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
#         headers = {
#             "xi-api-key": self.api_key,
#             "Content-Type": "application/json"
#         }
#         payload = {
#             "text": text,
#             "voice_settings": {"stability": 0.3, "similarity_boost": 0.75}
#         }

#         try:
#             resp = requests.post(url, json=payload, headers=headers, timeout=20)
#             resp.raise_for_status()
#             # ElevenLabs returns audio bytes (mp3) in body
#             audio_bytes = resp.content
#             logger.debug(f"Generated TTS audio ({len(audio_bytes)} bytes)")
#             return audio_bytes
#         except Exception as e:
#             logger.exception(f"ElevenLabs TTS error: {e}")
#             return None



# app/services/tts_service.py
# import logging
# import requests
# from typing import Optional

# logger = logging.getLogger(__name__)


# class TTSService:
#     """
#     Synthesize text to speech using ElevenLabs HTTP API (sync).
#     Returns raw audio bytes (mp3) that can be sent back to Twilio.
#     """

#     def __init__(self, api_key: str = None):
#         from ..core.config import settings
#         self.api_key = api_key or settings.ELEVENLABS_API_KEY
#         self.default_voice = getattr(__import__("os"), "environ").get("ELEVENLABS_VOICE_EN", None)

#     def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
#         if not self.api_key:
#             logger.warning("ElevenLabs API key not set; TTS disabled.")
#             return None

#         voice_id = voice or self.default_voice
#         if not voice_id:
#             logger.warning("No ElevenLabs voice specified.")
#             return None

#         url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
#         headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
#         payload = {"text": text, "voice_settings": {"stability": 0.3, "similarity_boost": 0.75}}

#         try:
#             resp = requests.post(url, json=payload, headers=headers, timeout=30)
#             resp.raise_for_status()
#             audio_bytes = resp.content
#             logger.debug(f"Generated TTS audio ({len(audio_bytes)} bytes)")
#             return audio_bytes
#         except Exception as e:
#             logger.exception(f"ElevenLabs TTS error: {e}")
#             return None


# app/services/tts_service.py
# import logging
# import requests
# from typing import Optional
# from pydub import AudioSegment
# import io

# logger = logging.getLogger(__name__)

# class TTSService:
#     """
#     ElevenLabs TTS → Convert MP3 → 8kHz μ-law PCM for Twilio Media Streams
#     """

#     def __init__(self, api_key: str = None):
#         from ..core.config import settings
#         self.api_key = api_key or settings.ELEVENLABS_API_KEY
#         self.default_voice = getattr(__import__("os"), "environ").get("ELEVENLABS_VOICE_EN", None)

#     def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
#         if not self.api_key:
#             logger.warning("ElevenLabs API key not set; TTS disabled.")
#             return None

#         voice_id = voice or self.default_voice
#         if not voice_id:
#             logger.warning("No ElevenLabs voice specified.")
#             return None

#         url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
#         headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
#         payload = {"text": text}

#         try:
#             # Request MP3 from ElevenLabs
#             resp = requests.post(url, json=payload, headers=headers, timeout=30)
#             resp.raise_for_status()
#             mp3_bytes = resp.content

#             # ---- Convert MP3 → PCM WAV → μ-law 8k ----

#             # Load MP3
#             mp3_audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")

#             # Convert to mono 8kHz 16-bit PCM
#             wav_audio = mp3_audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)

#             # Convert to μ-law (Twilio required)
#             ulaw_audio = wav_audio.set_sample_width(1)

#             raw_bytes = ulaw_audio.raw_data
#             logger.info(f"TTS μ-law audio generated: {len(raw_bytes)} bytes")

#             return raw_bytes

#         except Exception as e:
#             logger.exception(f"ElevenLabs TTS error: {e}")
#             return None

# app/services/tts_service.py
import logging
import requests
from typing import Optional
from pydub import AudioSegment
import io
import audioop  # builtin
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, api_key: str = None):
        from ..core.config import settings
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.default_voice = getattr(__import__("os"), "environ").get("ELEVENLABS_VOICE_EN", None)

    def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        if not self.api_key:
            logger.warning("ElevenLabs API key not set; TTS disabled.")
            return None

        voice_id = voice or self.default_voice
        if not voice_id:
            logger.warning("No ElevenLabs voice specified.")
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {"text": text}

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            mp3_bytes = resp.content

            # Convert MP3 -> raw 16-bit PCM at 8000Hz mono
            audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
            audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)

            # pydub raw_data is signed 16-bit little-endian PCM
            pcm16 = audio.raw_data  # bytes

            # Convert linear PCM16 -> 8-bit μ-law
            ulaw_bytes = audioop.lin2ulaw(pcm16, 2)  # width=2 for 16-bit input

            # ulaw_bytes is what Twilio expects as raw payload (8000Hz, μ-law)
            logger.info(f"TTS produced μ-law bytes: {len(ulaw_bytes)}")
            return ulaw_bytes

        except Exception as e:
            logger.exception(f"ElevenLabs TTS error: {e}")
            return None
