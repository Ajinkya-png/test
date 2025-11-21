# import asyncio
# import json
# import logging
# from deepgram import Deepgram
# from typing import Optional, Callable, Dict, Any
# from ..core.config import settings

# logger = logging.getLogger(__name__)


# class STTService:
#     """
#     Wrapper around Deepgram realtime and prerecorded transcription.
#     - transcribe_stream: expects an async iterator/generator of raw audio chunks (bytes or base64 depending on your streaming approach)
#     - transcribe_file: accepts a local audio file path and returns the final transcript
#     """
#     def __init__(self):
#         # Deepgram client uses an API key; library methods vary by SDK version.
#         self.dg_client = Deepgram(settings.DEEPGRAM_API_KEY)
#         self.is_connected = False

#     async def transcribe_stream(
#         self,
#         audio_stream,
#         on_transcript: Callable[[str, bool], None],
#         language: str = "en",
#         interim_results: bool = True
#     ):
#         """Real-time streaming transcription"""
#         try:
#             connection = await self.dg_client.transcription.live({
#                 'smart_format': True,
#                 'interim_results': interim_results,
#                 'language': language,
#                 'model': 'nova-2',
#                 'punctuate': True,
#                 'utterance_end_ms': 1000
#             })

#             self.is_connected = True

#             async def receive_transcripts():
#                 async for message in connection:
#                     try:
#                         data = json.loads(message)
#                     except Exception:
#                         # If message is already a dict, keep it
#                         data = message if isinstance(message, dict) else {}
#                     # Handle transcript
#                     if isinstance(data, dict) and 'channel' in data and 'alternatives' in data['channel']:
#                         transcript = data['channel']['alternatives'][0].get('transcript', '')
#                         is_final = data.get('is_final', False)

#                         if transcript.strip():
#                             on_transcript(transcript, is_final)

#                     # Handle connection errors
#                     if isinstance(data, dict) and data.get('msg') == 'error':
#                         logger.error(f"Deepgram error: {data}")
#                         break

#             # Send audio to Deepgram
#             async def send_audio():
#                 try:
#                     async for chunk in audio_stream:
#                         if connection:
#                             await connection.send(chunk)
#                 except Exception as e:
#                     logger.error(f"Error sending audio to Deepgram: {e}")
#                 finally:
#                     # finish or close the connection (SDK-specific)
#                     try:
#                         await connection.finish()
#                     except Exception:
#                         pass

#             # Run both tasks concurrently
#             await asyncio.gather(
#                 receive_transcripts(),
#                 send_audio()
#             )

#         except Exception as e:
#             logger.error(f"STT service error: {e}")
#             self.is_connected = False
#             raise

#     async def transcribe_file(self, audio_file_path: str, language: str = "en") -> Optional[str]:
#         """Transcribe an audio file using Deepgram prerecord API"""
#         try:
#             with open(audio_file_path, 'rb') as audio:
#                 source = {'buffer': audio, 'mimetype': 'audio/wav'}
#                 response = await self.dg_client.transcription.prerecorded(
#                     source,
#                     {
#                         'smart_format': True,
#                         'language': language,
#                         'model': 'nova-2'
#                     }
#                 )

#             # Response format may vary with Deepgram SDK versions
#             transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
#             return transcript
#         except Exception as e:
#             logger.error(f"File transcription error: {e}")
#             return None

# app/services/stt_service.py
# import logging
# import requests
# from typing import Optional

# logger = logging.getLogger(__name__)

# class STTService:
#     """
#     Lightweight per-chunk transcription using Deepgram's REST `/v1/listen` endpoint.
#     Not true streaming but low-latency enough for demo use.
#     """
#     def __init__(self, api_key: str = None):
#         from ..core.config import settings
#         self.api_key = api_key or settings.DEEPGRAM_API_KEY
#         self.endpoint = "https://api.deepgram.com/v1/listen"

#     def transcribe_bytes(self, audio_bytes: bytes, mimetype: str = "audio/wav") -> Optional[str]:
#         """
#         Send a chunk of audio bytes to Deepgram and return transcript (best effort).
#         audio_bytes: raw audio bytes (wav/pcm/ulaw) — Twilio sends μ-law base64 by default.
#         """
#         if not self.api_key:
#             logger.warning("Deepgram API key not set; returning None for transcript.")
#             return None

#         headers = {
#             "Authorization": f"Token {self.api_key}",
#             "Content-Type": mimetype,
#         }
#         params = {
#             "model": "general",   # or specify model param
#             # you can add lang or endpointing params here
#         }
#         try:
#             resp = requests.post(self.endpoint, params=params, headers=headers, data=audio_bytes, timeout=10)
#             resp.raise_for_status()
#             payload = resp.json()
#             # Deepgram v2 REST structure: payload["results"]["channels"][0]["alternatives"][0]["transcript"]
#             results = payload.get("results", {})
#             channels = results.get("channels", [])
#             if channels:
#                 alternatives = channels[0].get("alternatives", [])
#                 if alternatives:
#                     transcript = alternatives[0].get("transcript", "")
#                     logger.debug(f"Deepgram transcript: {transcript[:100]}")
#                     return transcript
#             return None
#         except Exception as e:
#             logger.exception(f"Deepgram transcription error: {e}")
#             return None



# app/services/stt_service.py
# import logging
# import requests
# from typing import Optional

# logger = logging.getLogger(__name__)


# class STTService:
#     """
#     Lightweight per-chunk transcription using Deepgram's REST `/v1/listen` endpoint.
#     """

#     def __init__(self, api_key: str = None):
#         from ..core.config import settings
#         self.api_key = api_key or settings.DEEPGRAM_API_KEY
#         self.endpoint = "https://api.deepgram.com/v1/listen"

#     def transcribe_bytes(self, audio_bytes: bytes, mimetype: str = "audio/wav") -> Optional[str]:
#         """
#         Send a chunk of audio bytes to Deepgram and return transcript (best effort).
#         """
#         if not self.api_key:
#             logger.warning("Deepgram API key not set; returning None for transcript.")
#             return None

#         headers = {
#             "Authorization": f"Token {self.api_key}",
#             "Content-Type": mimetype,
#         }
#         params = {"model": "general"}
#         try:
#             resp = requests.post(self.endpoint, params=params, headers=headers, data=audio_bytes, timeout=15)
#             resp.raise_for_status()
#             payload = resp.json()
#             results = payload.get("results", {})
#             channels = results.get("channels", [])
#             if channels:
#                 alternatives = channels[0].get("alternatives", [])
#                 if alternatives:
#                     transcript = alternatives[0].get("transcript", "")
#                     logger.debug(f"Deepgram transcript: {transcript[:120]}")
#                     return transcript
#             return None
#         except Exception as e:
#             logger.exception(f"Deepgram transcription error: {e}")
#             return None

#     # in app/services/stt_service.py (modify or add wrapper)
# def transcribe_base64_pcm(self, b64_payload: str) -> Optional[str]:
#     import base64
#     pcm_bytes = base64.b64decode(b64_payload)
#     wav_bytes = pcm16le_bytes_to_wav_bytes(pcm_bytes, sample_rate=8000)
#     return self.transcribe_bytes(wav_bytes, mimetype="audio/wav")



import logging
import asyncio
import websockets
import json
from typing import Optional, Callable, AsyncGenerator
import base64

logger = logging.getLogger(__name__)

class STTService:
    """Real-time streaming STT using Deepgram's WebSocket API"""
    
    def __init__(self, api_key: str = None):
        from ..core.config import settings
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self.websocket_url = "wss://api.deepgram.com/v1/listen"
        
    async def transcribe_stream(self, audio_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        """Real-time streaming transcription"""
        
        headers = {
            "Authorization": f"Token {self.api_key}",
        }
        
        params = {
            "model": "nova-2",
            "interim_results": "true",
            "endpointing": "500",  # End utterance after 500ms silence
            "vad_events": "true",  # Voice activity detection
            "punctuate": "true",
            "numerals": "true",
            "utterance_end_ms": "1000"  # End utterance after 1s silence
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.websocket_url}?{query_string}"
        
        try:
            async with websockets.connect(url, extra_headers=headers) as websocket:
                logger.info("Deepgram WebSocket connected")
                
                # Start audio sending task
                async def send_audio():
                    async for audio_chunk in audio_generator:
                        if audio_chunk:
                            await websocket.send(audio_chunk)
                    await websocket.send(json.dumps({"type": "CloseStream"}))
                
                send_task = asyncio.create_task(send_audio())
                
                # Receive transcriptions
                async for message in websocket:
                    data = json.loads(message)
                    
                    # Handle transcription results
                    if data.get("type") == "Results":
                        channel = data.get("channel", {})
                        alternatives = channel.get("alternatives", [])
                        
                        if alternatives:
                            transcript = alternatives[0].get("transcript", "").strip()
                            is_final = alternatives[0].get("confidence", 0) > 0.8
                            
                            if transcript and is_final:
                                logger.debug(f"Final transcript: {transcript}")
                                yield transcript
                
                await send_task
                
        except Exception as e:
            logger.error(f"Deepgram WebSocket error: {e}")
            raise

    def transcribe_bytes(self, audio_bytes: bytes, mimetype: str = "audio/wav") -> Optional[str]:
        """Fallback for single audio chunks"""
        import requests
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": mimetype,
        }
        
        params = {
            "model": "nova-2",
            "punctuate": "true",
            "numerals": "true",
            "endpointing": "500"
        }
        
        try:
            resp = requests.post(
                "https://api.deepgram.com/v1/listen", 
                params=params, 
                headers=headers, 
                data=audio_bytes, 
                timeout=10
            )
            resp.raise_for_status()
            payload = resp.json()
            
            results = payload.get("results", {})
            channels = results.get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    transcript = alternatives[0].get("transcript", "").strip()
                    logger.debug(f"Deepgram transcript: {transcript}")
                    return transcript
            return None
            
        except Exception as e:
            logger.error(f"Deepgram transcription error: {e}")
            return None

def pcm16le_bytes_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 8000) -> bytes:
    """Convert PCM bytes to WAV format"""
    import struct
    import io
    
    # WAV header
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_bytes)
    
    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',  # ChunkID
        36 + data_size,  # ChunkSize
        b'WAVE',  # Format
        b'fmt ',  # Subchunk1ID
        16,  # Subchunk1Size
        1,  # AudioFormat (PCM)
        num_channels,  # NumChannels
        sample_rate,  # SampleRate
        byte_rate,  # ByteRate
        block_align,  # BlockAlign
        bits_per_sample,  # BitsPerSample
        b'data',  # Subchunk2ID
        data_size  # Subchunk2Size
    )
    
    return wav_header + pcm_bytes