from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start
import logging
from typing import Optional, Dict, Any
from ..core.config import settings

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Wrapper around Twilio client for voice operations.
    """
    _client: Optional[Client] = None

    @classmethod
    def initialize(cls):
        """Initialize Twilio REST client"""
        if not cls._client:
            cls._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            logger.info("Twilio client initialized")

    @classmethod
    def get_client(cls) -> Client:
        if not cls._client:
            raise RuntimeError("Twilio client not initialized. Call TwilioService.initialize() first.")
        return cls._client

    # ----------------------------------------------------
    # 🔥 NEW: Get your Twilio phone number
    # ----------------------------------------------------
    @classmethod
    def get_default_from_number(cls) -> str:
        """
        Return your Twilio phone number.
        Works for:
        - Trial accounts
        - Paid accounts
        - Single-number accounts
        """
        client = cls.get_client()

        incoming_numbers = client.incoming_phone_numbers.list(limit=1)

        if not incoming_numbers:
            raise RuntimeError("❌ No Twilio incoming numbers found. Buy/verify a number in Twilio Console.")

        return incoming_numbers[0].phone_number

    # ----------------------------------------------------
    # Create TwiML for handling incoming calls
    # ----------------------------------------------------
    @classmethod
    def create_voice_response(cls, stream_url: str, status_callback: str = None) -> VoiceResponse:
        """Create TwiML for voice call with media stream"""
        response = VoiceResponse()

        start = Start()
        start.stream(
            url=stream_url,
            name="FoodDeliveryVoiceAI"
        )
        response.append(start)

        # Stub connect – call is handled via websocket stream
        # response.connect()

        return response
    
    @classmethod
    def create_voice_response(cls, stream_url: str, status_callback: str = None) -> VoiceResponse:
        """Create TwiML response for voice call with media streaming"""
        response = VoiceResponse()

        # Start media stream
        start = Start()
        start.stream(url=stream_url, name="FoodDeliveryVoiceAI")
        response.append(start)

        # Add greeting so Twilio does NOT fall back to keypad mode
        response.say("Hello! You are connected to the Food Delivery Voice Assistant.")
        response.pause(length=1)

        # Keep call open — no need for <Connect>
        return response


    # ----------------------------------------------------
    # Make outbound call
    # ----------------------------------------------------
    @classmethod
    def make_outbound_call(
        cls,
        to: str,
        from_: str,
        twiml_url: str,
        machine_detection: str = "Enable",
        status_callback: str = None
    ) -> Dict[str, Any]:

        client = cls.get_client()

        call = client.calls.create(
            to=to,
            from_=from_,
            url=twiml_url,
            machine_detection=machine_detection,
            status_callback=status_callback,
            status_callback_event=["initiated", "ringing", "answered", "completed"]
        )

        logger.info(f"Outbound call initiated: {call.sid}")
        return {
            "call_sid": call.sid,
            "status": call.status,
            "direction": call.direction
        }

    # ----------------------------------------------------
    # End call
    # ----------------------------------------------------
    @classmethod
    def end_call(cls, call_sid: str) -> bool:
        try:
            client = cls.get_client()
            client.calls(call_sid).update(status="completed")
            logger.info(f"Call ended: {call_sid}")
            return True
        except Exception as e:
            logger.error(f"Error ending call {call_sid}: {e}")
            return False

    # ----------------------------------------------------
    # Fetch call details
    # ----------------------------------------------------
    @classmethod
    def get_call_status(cls, call_sid: str) -> Optional[Dict[str, Any]]:
        try:
            client = cls.get_client()
            call = client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "duration": call.duration,
                "from": call.from_,
                "to": call.to,
                "start_time": call.start_time,
                "end_time": call.end_time
            }
        except Exception as e:
            logger.error(f"Error fetching call status {call_sid}: {e}")
            return None
    @classmethod
    def play_audio_on_call(cls, call_sid: str, play_url: str) -> bool:
        try:
            client = cls.get_client()
            client.calls(call_sid).update(twiml=f"<Response><Play>{play_url}</Play></Response>")
            return True
        except Exception as e:
            logger.exception(f"Error playing audio on call {call_sid}: {e}")
            return False
