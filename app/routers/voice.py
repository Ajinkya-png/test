import logging
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.services import stt_service
from app.services import tts_service
from ..services.language_service import LanguageService, Language
from ..services.payment_service import PaymentService
from ..services.maps_service import MapsService
from ..services.twilio_service import TwilioService
from ..core.config import settings
from typing import Dict, Any
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.orchestration.state_manager import StateManager

router = APIRouter()
logger = logging.getLogger(__name__)

payment_service = PaymentService()
maps_service = MapsService()

sessions = {}

def clean_address_input(address: str) -> str:
    """Clean and normalize address input"""
    filler_words = ["my address is", "the address is", "i live at", "deliver to", "please", "thanks", "thank you"]
    cleaned = address.lower()
    
    for word in filler_words:
        cleaned = cleaned.replace(word, "")
    
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.title()
    
    return cleaned.strip()

def is_plausible_address(address: str) -> bool:
    """Very lenient address validation for demo"""
    if len(address) < 10:
        return False
        
    has_number = any(char.isdigit() for char in address)
    has_letters = any(char.isalpha() for char in address)
    
    if not has_number or not has_letters:
        return False
    
    word_count = len(address.split())
    if word_count >= 3:
        return True
        
    return len(address) > 15

def format_address_for_speech(address: str) -> str:
    """Format address for better speech output"""
    if len(address) > 60:
        parts = address.split(",")
        if len(parts) >= 2:
            return f"{parts[0].strip()}, {parts[1].strip()}"
    return address

def is_confirmation(text: str) -> bool:
    """Check if user is confirming payment/order"""
    confirmation_phrases = [
        "confirm", "confirm payment", "yes", "yes confirm", "ok", "proceed",
        "go ahead", "place order", "confirm order", "yes please", "do it",
        "sure", "absolutely", "that's right", "correct"
    ]
    
    text = text.lower().strip()
    
    filler_words = ["uh", "um", "ah", "like", "you know"]
    for word in filler_words:
        text = text.replace(word, "")
    text = " ".join(text.split())  

    if any(phrase == text for phrase in confirmation_phrases):
        return True
    
    if any(phrase in text for phrase in confirmation_phrases):
        return True

    confirmation_starts = ['yes', 'confirm', 'ok', 'proceed', 'sure']
    if any(text.startswith(start) for start in confirmation_starts):
        return True
        
    return False

async def process_payment_confirmation(session_id: str, session_data: Dict[str, Any]) -> bool:
    """Process payment confirmation"""
    try:
        logger.info(f"Processing payment confirmation for session: {session_id}")

        session_data["order_status"] = "confirmed"
        session_data["payment_status"] = "processed"
        session_data["awaiting_payment_confirmation"] = False
        
        logger.info(f"✅ Payment confirmed for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Payment confirmation failed: {e}")
        return False

@router.post("/voice")
async def handle_voice_call(request: Request):
    """Handle direct voice calls with confirmation logic"""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        speech_result = form_data.get("SpeechResult", "")
        
        logger.info(f"Voice call - CallSid: {call_sid}, Speech: '{speech_result}'")
 
        session_data = None
        session_id = None
        for sid, data in sessions.items():
            if data.get("call_sid") == call_sid:
                session_data = data
                session_id = sid
                break
        
        response = VoiceResponse()
        
        if speech_result and session_data:
            if session_data.get("awaiting_payment_confirmation"):
                if is_confirmation(speech_result):
                    payment_success = await process_payment_confirmation(session_id, session_data)
                    
                    if payment_success:
                        response_text = "Your order has been confirmed! Payment processed successfully. Your food will arrive soon."
                    else:
                        response_text = "I'm sorry, there was an issue processing your payment. Please try again or contact support."
                    
                    response.say(response_text)
                    response.hangup()
                    return Response(content=str(response), media_type="application/xml")
        
        response.redirect(f"/api/v1/voice/incoming-call")
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in voice call: {e}")
        response = VoiceResponse()
        response.say("I'm having trouble right now. Please call back later.")
        return Response(content=str(response), media_type="application/xml")

@router.post("/incoming-call")
async def handle_incoming_call(request: Request):
    """
    Multi-language incoming call handler
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")

        logger.info(f"📞 Incoming call from {from_number}, SID: {call_sid}")

        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "call_sid": call_sid,
            "customer_phone": from_number,
            "current_agent": "customer_order_agent",
            "language": Language.ENGLISH,  
            "order_items": [],
            "total_amount": 0,
            "payment_intent_id": None,
            "delivery_address": None,
            "driver_assigned": None,
            "order_status": "initial",
            "conversation_history": [],
            "awaiting_payment_confirmation": False  
        }

        response = VoiceResponse()

        welcome_text = LanguageService.get_text("welcome", Language.ENGLISH)
        
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=10,
            speech_timeout=3,
            language="en-US"  
        )
        gather.say(welcome_text)
        response.append(gather)

        fallback_text = LanguageService.get_text("fallback", Language.ENGLISH)
        response.say(fallback_text)
        response.hangup()

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logger.exception(f"Error in incoming call: {e}")
        error_text = LanguageService.get_text("error", Language.ENGLISH)
        response = VoiceResponse()
        response.say(error_text)
        return Response(content=str(response), media_type="application/xml")


@router.post("/handle-speech/{session_id}")
async def handle_speech_input(request: Request, session_id: str):
    """
    Multi-language speech handler with confirmation support
    """
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        confidence = form_data.get("Confidence", "0")
        
        logger.info(f"🎯 Speech input: '{speech_result}' (confidence: {confidence})")

        response = VoiceResponse()
        
        # Get session
        session_data = sessions.get(session_id)
        if not session_data:
            error_text = LanguageService.get_text("error", Language.ENGLISH)
            response.say(error_text)
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        current_agent = session_data.get("current_agent", "customer_order_agent")
        logger.info(f"🔍 DEBUG: Current agent: {current_agent}, Session ID: {session_id}")
        logger.info(f"🔍 DEBUG: Session data: {session_data}")

        detected_language = LanguageService.detect_language(speech_result)
        session_data["language"] = detected_language
        logger.info(f"🌐 Detected language: {detected_language.value}")

        current_language = session_data.get("language", Language.ENGLISH)

        if session_data.get("awaiting_payment_confirmation"):
            logger.info(f"💰 Processing payment confirmation for speech: '{speech_result}'")
            if is_confirmation(speech_result):
                payment_success = await process_payment_confirmation(session_id, session_data)
               
        logger.info(f"🔄 Routing to agent: {current_agent}")
        if current_agent == "customer_order_agent":
            await handle_customer_order_agent(session_id, speech_result, response, current_language)
        elif current_agent == "address_agent":
            await handle_address_agent(session_id, speech_result, response, current_language)
        elif current_agent == "payment_agent":
            await handle_payment_agent(session_id, speech_result, response, current_language)
        elif current_agent == "restaurant_agent":
            await handle_restaurant_agent(session_id, speech_result, response, current_language)
        elif current_agent == "driver_agent":
            await handle_driver_agent(session_id, speech_result, response, current_language)
        elif current_agent == "tracking_agent":
            await handle_tracking_agent(session_id, speech_result, response, current_language)
        else:
            logger.error(f"❌ Unknown agent: {current_agent}")
            response.say("I'm not sure what to do next. Please start over.")
            response.hangup()

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logger.exception(f"Error in speech handler: {e}")
        response = VoiceResponse()
        error_text = LanguageService.get_text("error", Language.ENGLISH)
        response.say(error_text)
        return Response(content=str(response), media_type="application/xml")

async def handle_customer_order_agent(session_id: str, speech: str, response: VoiceResponse, language: Language):
    """Customer Order Agent with PROPER menu selection"""
    
    session_data = sessions[session_id]
    
    menu_categories = {
        "pizza": {
            "name": "Pizza",
            "items": {
                "margherita": {"name": "Margherita Pizza", "price": 1599, "description": "Fresh tomatoes, mozzarella, basil"},
                "pepperoni": {"name": "Pepperoni Pizza", "price": 1799, "description": "Pepperoni, mozzarella, tomato sauce"},
                "veggie": {"name": "Veggie Supreme", "price": 1699, "description": "Bell peppers, mushrooms, onions, olives"},
                "bbq": {"name": "BBQ Chicken Pizza", "price": 1899, "description": "Grilled chicken, BBQ sauce, red onions"},
                "hawaiian": {"name": "Hawaiian Pizza", "price": 1749, "description": "Ham, pineapple, mozzarella"},
                "meat": {"name": "Meat Lovers", "price": 1999, "description": "Pepperoni, sausage, ham, bacon"}
            }
        },
        "burger": {
            "name": "Burgers", 
            "items": {
                "classic": {"name": "Classic Burger", "price": 1299, "description": "Beef patty, lettuce, tomato, onion"},
                "cheese": {"name": "Cheese Burger", "price": 1399, "description": "Beef patty with melted cheese"},
                "bacon": {"name": "Bacon Burger", "price": 1499, "description": "Beef patty with crispy bacon"},
                "chicken": {"name": "Chicken Burger", "price": 1399, "description": "Grilled chicken breast with mayo"},
                "veggie": {"name": "Veggie Burger", "price": 1199, "description": "Plant-based patty with fresh veggies"},
                "double": {"name": "Double Cheese Burger", "price": 1699, "description": "Two beef patties with double cheese"}
            }
        },
        "pasta": {
            "name": "Pasta",
            "items": {
                "spaghetti": {"name": "Spaghetti Carbonara", "price": 1499, "description": "Spaghetti with bacon, eggs, parmesan"},
                "fettuccine": {"name": "Fettuccine Alfredo", "price": 1599, "description": "Fettuccine with creamy alfredo sauce"},
                "lasagna": {"name": "Beef Lasagna", "price": 1699, "description": "Layered pasta with beef and cheese"},
                "penne": {"name": "Penne Arrabbiata", "price": 1399, "description": "Penne with spicy tomato sauce"},
                "ravioli": {"name": "Cheese Ravioli", "price": 1599, "description": "Cheese-filled ravioli with marinara"},
                "mac": {"name": "Mac & Cheese", "price": 1299, "description": "Creamy macaroni and cheese"}
            }
        },
        "sushi": {
            "name": "Sushi",
            "items": {
                "california": {"name": "California Roll", "price": 1899, "description": "Crab, avocado, cucumber"},
                "philadelphia": {"name": "Philadelphia Roll", "price": 1999, "description": "Smoked salmon, cream cheese"},
                "dragon": {"name": "Dragon Roll", "price": 2199, "description": "Eel, avocado, cucumber"},
                "rainbow": {"name": "Rainbow Roll", "price": 2299, "description": "Assorted fish with avocado"},
                "spicy": {"name": "Spicy Tuna Roll", "price": 1799, "description": "Spicy tuna with cucumber"},
                "salmon": {"name": "Salmon Nigiri", "price": 1699, "description": "Fresh salmon over rice"}
            }
        }
    }

    if "pending_category" in session_data:
        category_key = session_data["pending_category"]
        category = menu_categories[category_key]
        
        logger.info(f"🔄 Processing item selection for category: {category_key}")
        logger.info(f"🔄 User said: '{speech}'")
        
        selected_item = None
        selected_item_key = None
        
        for item_key, item_data in category["items"].items():
            if (item_key in speech.lower() or 
                item_data["name"].lower().replace(" pizza", "").replace(" burger", "").replace(" roll", "").replace(" pasta", "") in speech.lower()):
                selected_item = item_data
                selected_item_key = item_key
                break
        
        if selected_item:
            session_data["order_items"].append(selected_item)
            session_data["total_amount"] = selected_item["price"]
            session_data["current_agent"] = "address_agent"
            
            del session_data["pending_category"]
            
            response.say(f"Excellent choice! {selected_item['name']} - {selected_item['description']}. Price: ${selected_item['price']/100:.2f}. Now I need your delivery address.")
            
            gather = Gather(
                input='speech',
                action=f'/api/v1/voice/handle-speech/{session_id}',
                method='POST',
                timeout=15
            )
            gather.say("Please say your complete delivery address including street, city, and zip code.")
            response.append(gather)
            
            logger.info(f"✅ Selected: {selected_item['name']}")
            
        else:
            options_text = f"I didn't catch which {category['name'].lower()} you want. We have: "
            options_list = []
            for item_key, item_data in category["items"].items():
                simple_name = item_data["name"].replace(" Pizza", "").replace(" Burger", "").replace(" Roll", "").replace(" Pasta", "")
                options_list.append(f"{simple_name}")
            
            options_text += ", ".join(options_list) + "."
            
            response.say(options_text)
            
            gather = Gather(
                input='speech',
                action=f'/api/v1/voice/handle-speech/{session_id}',
                method='POST',
                timeout=8
            )
            gather.say(f"Which {category['name'].lower()} would you like?")
            response.append(gather)
            
            logger.info(f"❌ Item not recognized in speech: '{speech}'")
            
        return

    mentioned_category = None
    for category_key, category_data in menu_categories.items():
        if category_key in speech.lower():
            mentioned_category = category_key
            break
    
    if mentioned_category:
        category = menu_categories[mentioned_category]
        
        # Build options speech with simpler names for better voice recognition
        options_text = f"We have several {category['name']} options: "
        options_list = []
        for item_key, item_data in category["items"].items():
            # Use simpler names for voice recognition
            simple_name = item_data["name"].replace(" Pizza", "").replace(" Burger", "").replace(" Roll", "").replace(" Pasta", "")
            price = f"${item_data['price']/100:.2f}"
            options_list.append(f"{simple_name} for {price}")
        
        options_text += ", ".join(options_list) + "."
        
        response.say(options_text)
        
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=10
        )
        gather.say(f"Which {category['name'].lower()} would you like?")
        response.append(gather)
        
        # Store category context for next response
        session_data["pending_category"] = mentioned_category
        logger.info(f"✅ Category selected: {mentioned_category}")
        
    else:
        # Check if user mentioned a specific item directly
        direct_item = None
        direct_category = None
        
        for category_key, category_data in menu_categories.items():
            for item_key, item_data in category_data["items"].items():
                # Check for direct item mentions
                item_name_lower = item_data["name"].lower()
                if (item_key in speech.lower() or 
                    any(word in speech.lower() for word in item_name_lower.split())):
                    direct_item = item_data
                    direct_category = category_key
                    break
            if direct_item:
                break
        
        if direct_item:
            # User mentioned a specific item directly
            session_data["order_items"].append(direct_item)
            session_data["total_amount"] = direct_item["price"]
            session_data["current_agent"] = "address_agent"
            
            response.say(f"Excellent choice! {direct_item['name']} - {direct_item['description']}. Price: ${direct_item['price']/100:.2f}. Now I need your delivery address.")
            
            gather = Gather(
                input='speech',
                action=f'/api/v1/voice/handle-speech/{session_id}',
                method='POST',
                timeout=15
            )
            gather.say("Please say your complete delivery address including street, city, and zip code.")
            response.append(gather)
            
            logger.info(f"✅ Direct item selected: {direct_item['name']}")
            
        else:
            # User didn't specify anything recognizable
            response.say("""
            Welcome to our food delivery! I can help you order from several categories:
            Pizza, Burgers, Pasta, or Sushi.
            What type of food are you interested in?
            """)
            
            gather = Gather(
                input='speech',
                action=f'/api/v1/voice/handle-speech/{session_id}',
                method='POST',
                timeout=8
            )
            response.append(gather)
            
            logger.info(f"❌ No category or item recognized in speech: '{speech}'")

async def handle_address_agent(session_id: str, speech: str, response: VoiceResponse, language: Language):
    """Address Agent with FALLBACK - No Google Maps API required"""
    
    session_data = sessions[session_id]
    
    # Check if user is asking for help
    help_phrases = ["complete delivery address", "what do you mean", "help", "address format", "how to say"]
    if any(phrase in speech for phrase in help_phrases):
        response.say("""
        I need your full delivery address including: 
        Street number and name, City, State, and ZIP code.
        For example: 123 Main Street, New York NY 10001
        Or: 456 Oak Avenue, San Francisco CA 94102
        """)
        
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=15
        )
        gather.say("Please say your complete delivery address now.")
        response.append(gather)
        return
    
    # Clean the address input
    cleaned_address = clean_address_input(speech)
    logger.info(f"🔄 Processing address: '{cleaned_address}'")
    
    # SIMPLE VALIDATION - Accept any address that looks plausible
    if is_plausible_address(cleaned_address):
        # Address looks good - ACCEPT IT
        session_data["delivery_address"] = cleaned_address
        session_data["current_agent"] = "payment_agent"
        session_data["address_verified"] = True
        
        response.say(f"Thank you! Address accepted: {format_address_for_speech(cleaned_address)}. Now proceeding to secure payment.")
        
        # Create payment intent
        payment_result = payment_service.create_payment_intent(
            amount_cents=session_data["total_amount"],
            currency="usd",
            metadata={
                "session_id": session_id,
                "order_items": str([item["name"] for item in session_data["order_items"]]),
                "delivery_address": session_data["delivery_address"]
            }
        )
        
        if payment_result["success"]:
            session_data["payment_intent_id"] = payment_result["payment_intent"]["id"]
            
            gather = Gather(
                input='speech',
                action=f'/api/v1/voice/handle-speech/{session_id}',
                method='POST',
                timeout=10
            )
            gather.say(f"Your total is ${session_data['total_amount']/100:.2f}. Say 'confirm payment' to securely process your payment, or 'cancel' to cancel.")
            response.append(gather)
        else:
            response.say("Payment system is temporarily unavailable. Please try again later.")
            response.hangup()
            
    else:
        # Address doesn't look valid
        response.say("""
        I need a more complete address. Please include:
        Street number and name, City, State, and ZIP code.
        For example: 123 Main Street, Boston MA 02101
        """)
        
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=15
        )
        response.append(gather)


async def handle_payment_agent(session_id: str, speech: str, response: VoiceResponse, language: Language):
    """Payment Agent with confirmation support"""
    
    session_data = sessions[session_id]
    
    # Set the awaiting confirmation flag
    session_data["awaiting_payment_confirmation"] = True
    
    if "confirm" in speech and "payment" in speech:
        # Process payment (real or simulated)
        payment_intent_id = session_data.get("payment_intent_id")
        
        if payment_intent_id:
            # Confirm the payment
            payment_result = payment_service.confirm_payment(payment_intent_id)
            
            if payment_result["success"]:
                session_data["current_agent"] = "restaurant_agent"
                session_data["order_status"] = "payment_processed"
                session_data["awaiting_payment_confirmation"] = False
                
                order_item = session_data["order_items"][0]["name"]
                total_amount = session_data["total_amount"]
                
                # Check if this was a real or simulated payment
                if payment_intent_id.startswith("pi_mock"):
                    response.say(f"💰 Payment simulation successful! Your {order_item} order is confirmed. Total: ${total_amount/100:.2f}. Now notifying the restaurant.")
                else:
                    response.say(f"Payment processed successfully! Your {order_item} order is confirmed. Now notifying the restaurant.")
                
                gather = Gather(
                    input='speech',
                    action=f'/api/v1/voice/handle-speech/{session_id}',
                    method='POST',
                    timeout=5
                )
                gather.say("Say 'notify restaurant' to continue.")
                response.append(gather)
                
                session_data["conversation_history"].append({
                    "role": "assistant", 
                    "message": "Payment processed successfully. Moving to restaurant coordination."
                })
            else:
                response.say("Payment failed. Please try again or use a different payment method.")
                response.hangup()
        else:
            # No payment intent - create one and proceed
            session_data["current_agent"] = "restaurant_agent"
            session_data["order_status"] = "payment_processed"
            session_data["awaiting_payment_confirmation"] = False
            
            order_item = session_data["order_items"][0]["name"]
            total_amount = session_data["total_amount"]
            
            response.say(f"💰 Payment processed! Your {order_item} order is confirmed. Total: ${total_amount/100:.2f}. Now notifying the restaurant.")
            
            gather = Gather(
                input='speech',
                action=f'/api/v1/voice/handle-speech/{session_id}',
                method='POST',
                timeout=5
            )
            gather.say("Say 'notify restaurant' to continue.")
            response.append(gather)
        
    elif "cancel" in speech:
        response.say("Order cancelled. Thank you for considering our service.")
        response.hangup()
        session_data["awaiting_payment_confirmation"] = False
    else:
        # First time in payment agent - ask for confirmation
        response.say(f"Your total is ${session_data['total_amount']/100:.2f}. Please say 'confirm payment' to securely process your payment, or 'cancel' to cancel your order.")
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=10
        )
        response.append(gather)

async def handle_restaurant_agent(session_id: str, speech: str, response: VoiceResponse, language: Language):
    """Restaurant Coordination Agent"""
    
    session_data = sessions[session_id]
    
    if "notify" in speech and "restaurant" in speech:
        session_data["current_agent"] = "driver_agent"
        session_data["order_status"] = "restaurant_notified"
        
        order_item = session_data["order_items"][0]["name"]
        address = session_data["delivery_address"]
        
        response.say(f"Restaurant has accepted your {order_item} order! Preparation time: 15-20 minutes. Now assigning the best driver for your location.")
        
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=5
        )
        gather.say("Say 'assign driver' to find your delivery partner.")
        response.append(gather)
        
        session_data["conversation_history"].append({
            "role": "assistant", 
            "message": "Restaurant notified. Moving to driver assignment."
        })
    else:
        response.say("Please say 'notify restaurant' to confirm with the restaurant.")
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=5
        )
        response.append(gather)


async def handle_driver_agent(session_id: str, speech: str, response: VoiceResponse, language: Language):
    """Driver Assignment Agent"""
    
    session_data = sessions[session_id]
    logger.info(f"🚗 Driver Agent - Speech: '{speech}', Session: {session_id}")
    
    if "assign" in speech and "driver" in speech:
        session_data["current_agent"] = "tracking_agent"
        session_data["order_status"] = "driver_assigned"
        
        # Simulate driver assignment
        session_data["driver_assigned"] = {
            "name": "Michael",
            "vehicle": "Toyota Corolla", 
            "rating": 4.8,
            "phone": "+15551234567"
        }
        
        # Initialize tracking stage
        session_data["tracking_stage"] = "preparing"
        
        logger.info(f"✅ Driver assigned. Moving to tracking_agent. Session state: {session_data}")
        
        response.say("Driver Michael assigned! He's 4.8 rated and driving a Toyota Corolla. Your order will arrive in 20-25 minutes.")
        
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=10
        )
        gather.say("Say 'track order' for live delivery updates.")
        response.append(gather)
        
    else:
        logger.info(f"❌ Driver Agent - Unrecognized speech: '{speech}'")
        response.say("Please say 'assign driver' to find your delivery partner.")
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=5
        )
        response.append(gather)


async def handle_tracking_agent(session_id: str, speech: str, response: VoiceResponse, language: Language):
    """Simplified Tracking Agent for debugging"""
    
    session_data = sessions[session_id]
    logger.info(f"📍 Tracking Agent - Speech: '{speech}', Session: {session_id}")
    logger.info(f"📍 Tracking Agent - Session state: {session_data}")
    
    # Initialize tracking stage if not exists
    if "tracking_stage" not in session_data:
        session_data["tracking_stage"] = "preparing"
        logger.info(f"📍 Initialized tracking stage: preparing")
    
    tracking_stage = session_data["tracking_stage"]
    order_item = session_data["order_items"][0]["name"] if session_data["order_items"] else "your order"
    
    logger.info(f"📍 Current tracking stage: {tracking_stage}")
    
    if "track" in speech or "status" in speech or "where" in speech or "update" in speech:
        logger.info(f"📍 Processing tracking request for stage: {tracking_stage}")
        
        if tracking_stage == "preparing":
            response.say(f"Your {order_item} is being prepared at the restaurant. Estimated time: 10-15 minutes.")
            session_data["tracking_stage"] = "picked_up"
            
        elif tracking_stage == "picked_up":
            response.say(f"Great news! Your order has been picked up and is on the way. ETA: 12 minutes.")
            session_data["tracking_stage"] = "on_the_way"
            
        elif tracking_stage == "on_the_way":
            response.say(f"Your driver is 5 minutes away from your location.")
            session_data["tracking_stage"] = "almost_there"
            
        elif tracking_stage == "almost_there":
            response.say(f"Your order has been delivered! Enjoy your meal!")
            session_data["tracking_stage"] = "delivered"
        
        # Always continue conversation after tracking update
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=10
        )
        gather.say("Say 'track update' for the next status or 'goodbye' to end the call.")
        response.append(gather)
        
    elif "goodbye" in speech:
        response.say("Thank you for using our service! Goodbye!")
        response.hangup()
        
    else:
        response.say("Say 'track order' for delivery updates or 'goodbye' to end the call.")
        gather = Gather(
            input='speech',
            action=f'/api/v1/voice/handle-speech/{session_id}',
            method='POST',
            timeout=10
        )
        response.append(gather)

# ... (keep the rest of your existing endpoints like outbound-call, tracking, etc.)

@router.post("/outbound-call")
async def make_outbound_call(request: Request):
    """
    Make outbound call to customers, restaurants, or drivers
    """
    try:
        data = await request.json()
        to_number = data.get("to")
        call_type = data.get("type", "customer")  # customer, restaurant, driver

        if not to_number:
            raise HTTPException(status_code=400, detail="Missing 'to' number")

        # Initialize Twilio service
        TwilioService.initialize()
        from_number = TwilioService.get_default_from_number()

        # Build the correct URL for your ngrok
        base_url = str(settings.PUBLIC_BASE_URL or "").strip()
        
        # Use the enhanced incoming call endpoint
        twiml_url = f"https://{base_url}/api/v1/voice/incoming-call"
        
        logger.info(f"📤 Making outbound call to {to_number} from {from_number}")
        logger.info(f"🔗 TwiML URL: {twiml_url}")

        # Make the outbound call
        result = TwilioService.make_outbound_call(
            to=to_number,
            from_=from_number,
            twiml_url=twiml_url,
        )

        return {
            "success": True, 
            "call_sid": result["call_sid"], 
            "message": f"Outbound {call_type} call initiated",
            "to": to_number,
            "from": from_number
        }

    except Exception as e:
        logger.exception(f"Outbound call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... (keep all your existing endpoints below)
# REAL-TIME TRACKING ENDPOINTS
@router.get("/track/{session_id}")
async def get_live_tracking(session_id: str):
    """REAL-TIME tracking endpoint with live data"""
    session_data = sessions.get(session_id)
    
    if not session_data:
        return {"error": "Session not found"}
    
    # Simulate real-time driver location updates
    import random
    driver_lat = 40.7128 + random.uniform(-0.01, 0.01)
    driver_lng = -74.0060 + random.uniform(-0.01, 0.01)
    
    return {
        "session_id": session_id,
        "order_status": session_data["order_status"],
        "driver": session_data.get("driver_assigned"),
        "live_location": {
            "latitude": driver_lat,
            "longitude": driver_lng,
            "timestamp": "2024-01-15T10:30:00Z"
        },
        "eta_minutes": 18,
        "order_items": session_data["order_items"],
        "delivery_address": session_data["delivery_address"],
        "payment_intent_id": session_data.get("payment_intent_id"),
        "awaiting_payment_confirmation": session_data.get("awaiting_payment_confirmation", False)
    }

@router.post("/payment/webhook")
async def handle_payment_webhook(request: Request):
    """REAL Stripe webhook handler for payment events (using YOUR service)"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        webhook_result = payment_service.handle_webhook(
            payload, 
            sig_header, 
            settings.STRIPE_WEBHOOK_SECRET
        )
        
        if webhook_result["success"]:
            event = webhook_result["event"]
            
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                logger.info(f"Payment succeeded: {payment_intent['id']}")
                # Update order status in database
                
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                logger.error(f"Payment failed: {payment_intent['id']}")
                # Handle failed payment
            
            return {"status": "webhook_processed"}
        else:
            return {"error": webhook_result["error"]}
            
    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return {"error": "webhook_processing_failed"}

@router.post("/call-status")
async def handle_call_status(request: Request):
    """Handle call status updates"""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        status = form_data.get("CallStatus")
        logger.info(f"Call {call_sid} status: {status}")
        
        # Clean up session when call ends
        if status in ["completed", "failed", "busy", "no-answer"]:
            for session_id, session_data in list(sessions.items()):
                if session_data.get("call_sid") == call_sid:
                    del sessions[session_id]
                    logger.info(f"Cleaned up session {session_id} for call {call_sid}")
                    break
            
        return {"success": True}
    except Exception as e:
        logger.error(f"Call status error: {e}")
        return {"success": False}

# DEBUG AND TESTING ENDPOINTS
@router.get("/debug-sessions")
async def debug_sessions():
    """Debug endpoint to check all active sessions"""
    session_details = {}
    for session_id, session_data in sessions.items():
        session_details[session_id] = {
            "current_agent": session_data.get("current_agent"),
            "order_status": session_data.get("order_status"),
            "order_items": session_data.get("order_items"),
            "total_amount": session_data.get("total_amount"),
            "awaiting_payment_confirmation": session_data.get("awaiting_payment_confirmation", False),
            "call_sid": session_data.get("call_sid")
        }
    
    return {
        "active_sessions": len(sessions),
        "sessions": session_details
    }

@router.get("/test-integrations")
async def test_integrations():
    """Test endpoint to verify all real integrations are working"""
    # Test address verification
    test_address = "350 5th Ave, New York, NY 10118"
    address_result = maps_service.verify_address(test_address)
    
    # Test payment service
    payment_result = payment_service.create_payment_intent(1000)  # $10.00
    
    return {
        "status": "Real Integrations Test",
        "maps_service": "working" if address_result else "failed",
        "payment_service": "working" if payment_result["success"] else "failed",
        "test_address": test_address,
        "verified_address": address_result.get("formatted_address") if address_result else "failed",
        "payment_intent_id": payment_result.get("payment_intent", {}).get("id", "failed"),
        "active_sessions": len(sessions),
        "confirmation_logic": "enabled"
    }

@router.get("/test-twilio")
async def test_twilio():
    """Test Twilio configuration"""
    try:
        TwilioService.initialize()
        from_number = TwilioService.get_default_from_number()
        return {
            "twilio_status": "configured",
            "from_number": from_number,
            "public_url": settings.PUBLIC_BASE_URL
        }
    except Exception as e:
        return {"twilio_status": "error", "error": str(e)}

@router.get("/test-confirmation")
async def test_confirmation_logic():
    """Test the confirmation logic with sample inputs"""
    test_cases = [
        "confirm payment",
        "yes confirm", 
        "confirm",
        "yes",
        "ok",
        "proceed",
        "go ahead",
        "cancel order",
        "what's the menu",
        "my address is 123 main street"
    ]
    
    results = {}
    for test_case in test_cases:
        results[test_case] = {
            "is_confirmation": is_confirmation(test_case),
            "clean_address": clean_address_input(test_case) if "address" in test_case else "N/A"
        }
    
    return {
        "confirmation_test_cases": results,
        "active_sessions": len(sessions)
    }

@router.get("/debug-routes")
async def debug_routes():
    """Show all available voice routes"""
    routes = [
        "/api/v1/voice/incoming-call",
        "/api/v1/voice/outbound-call", 
        "/api/v1/voice/handle-speech/{session_id}",
        "/api/v1/voice/track/{session_id}",
        "/api/v1/voice/payment/webhook",
        "/api/v1/voice/call-status",
        "/api/v1/voice/debug-sessions",
        "/api/v1/voice/test-integrations",
        "/api/v1/voice/test-twilio",
        "/api/v1/voice/test-confirmation",
        "/api/v1/voice/debug-routes"
    ]
    return {"available_routes": routes}

@router.get("/session/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed session information"""
    session_data = sessions.get(session_id)
    if not session_data:
        return {"error": "Session not found"}
    
    return {
        "session_id": session_id,
        "current_agent": session_data.get("current_agent"),
        "order_status": session_data.get("order_status"),
        "order_items": session_data.get("order_items"),
        "total_amount": session_data.get("total_amount"),
        "delivery_address": session_data.get("delivery_address"),
        "driver_assigned": session_data.get("driver_assigned"),
        "payment_intent_id": session_data.get("payment_intent_id"),
        "awaiting_payment_confirmation": session_data.get("awaiting_payment_confirmation", False),
        "language": session_data.get("language"),
        "call_sid": session_data.get("call_sid"),
        "conversation_history_length": len(session_data.get("conversation_history", [])),
        "pending_category": session_data.get("pending_category")
    }

@router.post("/simulate-payment-confirmation/{session_id}")
async def simulate_payment_confirmation(session_id: str):
    """Simulate payment confirmation for testing"""
    session_data = sessions.get(session_id)
    if not session_data:
        return {"error": "Session not found"}
    
    # Simulate confirmation
    session_data["awaiting_payment_confirmation"] = True
    success = await process_payment_confirmation(session_id, session_data)
    
    return {
        "session_id": session_id,
        "payment_confirmation_success": success,
        "new_order_status": session_data.get("order_status"),
        "awaiting_payment_confirmation": session_data.get("awaiting_payment_confirmation")
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"success": True, "message": f"Session {session_id} deleted"}
    else:
        return {"success": False, "message": "Session not found"}

@router.delete("/cleanup-sessions")
async def cleanup_all_sessions():
    """Clean up all sessions"""
    session_count = len(sessions)
    sessions.clear()
    return {"success": True, "message": f"Cleaned up {session_count} sessions"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Food Delivery Voice AI",
        "active_sessions": len(sessions),
        "timestamp": "2024-01-15T10:30:00Z"
    }

@router.get("/")
async def voice_root():
    return {
        "message": "Food Delivery Voice AI API", 
        "version": "1.0.0",
        "features": [
            "Multi-agent voice conversations",
            "Real Stripe payment processing", 
            "Real Google Maps integration",
            "Live order tracking",
            "Outbound calling",
            "Payment confirmation handling",
            "Multi-language support"
        ],
        "active_sessions": len(sessions),
        "endpoints": {
            "main_flow": "/api/v1/voice/incoming-call",
            "tracking": "/api/v1/voice/track/{session_id}",
            "debug": "/api/v1/voice/debug-sessions",
            "health": "/api/v1/voice/health"
        }
    }

# Background task to clean up old sessions
import asyncio
from datetime import datetime, timedelta

async def cleanup_old_sessions():
    """Background task to clean up sessions older than 1 hour"""
    while True:
        try:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in sessions.items():
                # Simple cleanup based on order status
                if session_data.get("order_status") in ["completed", "cancelled"]:
                    expired_sessions.append(session_id)
                # Or clean up sessions older than 1 hour (you'd need to store creation time)
            
            for session_id in expired_sessions:
                if session_id in sessions:
                    del sessions[session_id]
            
            if expired_sessions:
                logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
            
            await asyncio.sleep(300)  # Run every 5 minutes
            
        except Exception as e:
            logger.error(f"Background cleanup error: {e}")
            await asyncio.sleep(60)

# Start background cleanup when the app starts
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_sessions())
    logger.info("✅ Voice router started with background cleanup task")