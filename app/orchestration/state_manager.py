# app/orchestration/state_manager.py
import json
import uuid
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StateManager:
    """
    FALLBACK VERSION - Uses in-memory storage instead of Redis
    This will work immediately without Redis dependencies
    """

    # In-memory storage (fallback)
    _sessions = {}
    _call_to_session = {}

    SESSION_TTL = timedelta(hours=1)

    @staticmethod
    async def create_session(call_sid: str, phone_number: str) -> str:
        """Create a new call session in memory"""
        try:
            session_id = str(uuid.uuid4())

            now_iso = datetime.utcnow().isoformat()
            session_data = {
                "session_id": session_id,
                "call_sid": call_sid,
                "customer_phone": phone_number,
                "current_agent": "customer_order_agent",
                "call_type": "inbound_customer",
                "start_time": now_iso,
                "last_activity": now_iso,
                "order_items": [],
                "agent_transitions": [],
                "interrupt_flag": False,
                "conversation_history": []
            }

            # Store in memory
            StateManager._sessions[session_id] = session_data
            StateManager._call_to_session[call_sid] = session_id

            logger.info(f"✅ CREATED SESSION (IN-MEMORY): {session_id} for call {call_sid}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}")
            # Return a simple session ID
            return f"simple-{call_sid}"

    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from memory"""
        try:
            session_data = StateManager._sessions.get(session_id)
            if session_data:
                # Update last activity
                session_data["last_activity"] = datetime.utcnow().isoformat()
                return session_data
            return None
        except Exception as e:
            logger.error(f"❌ Error getting session {session_id}: {e}")
            return None

    @staticmethod
    async def get_session_by_call_sid(call_sid: str) -> Optional[Dict[str, Any]]:
        """Get session data by call_sid"""
        try:
            session_id = StateManager._call_to_session.get(call_sid)
            if session_id:
                return await StateManager.get_session(session_id)
            return None
        except Exception as e:
            logger.error(f"❌ Error getting session by call_sid {call_sid}: {e}")
            return None

    @staticmethod
    async def update_session(session_id: str, **updates):
        """Update session data in memory - SIMPLE AND RELIABLE"""
        try:
            session_data = StateManager._sessions.get(session_id)
            if session_data:
                # Apply updates
                for key, value in updates.items():
                    session_data[key] = value
                
                session_data["last_activity"] = datetime.utcnow().isoformat()
                logger.info(f"✅ UPDATED SESSION: {session_id} with {list(updates.keys())}")
                return True
            else:
                logger.error(f"❌ Session {session_id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating session {session_id}: {e}")
            return False

    @staticmethod
    async def end_session(session_id: str):
        """End a session in memory"""
        try:
            session_data = StateManager._sessions.get(session_id)
            if session_data:
                call_sid = session_data.get("call_sid")
                
                # Remove from memory
                if session_id in StateManager._sessions:
                    del StateManager._sessions[session_id]
                if call_sid and call_sid in StateManager._call_to_session:
                    del StateManager._call_to_session[call_sid]

                logger.info(f"✅ ENDED SESSION: {session_id}")
            else:
                logger.warning(f"Session {session_id} not found for ending")
        except Exception as e:
            logger.error(f"❌ Error ending session {session_id}: {e}")

    @staticmethod
    async def end_session_by_call_sid(call_sid: str):
        """End session using Twilio CallSid mapping"""
        try:
            session_id = StateManager._call_to_session.get(call_sid)
            if session_id:
                await StateManager.end_session(session_id)
            else:
                logger.warning(f"No session found for call_sid {call_sid}")
        except Exception as e:
            logger.error(f"❌ Error ending session by call SID {call_sid}: {e}")

    @staticmethod
    async def add_conversation_turn(session_id: str, role: str, message: str):
        """Add a conversation turn to history"""
        try:
            session_data = StateManager._sessions.get(session_id)
            if session_data:
                turn = {
                    "role": role,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Ensure conversation_history exists
                if "conversation_history" not in session_data:
                    session_data["conversation_history"] = []
                
                session_data["conversation_history"].append(turn)
                logger.info(f"✅ ADDED CONVERSATION TURN: {role} - {message[:50]}...")
                
        except Exception as e:
            logger.error(f"❌ Error adding conversation turn for session {session_id}: {e}")

    @staticmethod
    async def debug_session(session_id: str) -> Dict[str, Any]:
        """Debug method to inspect session state"""
        try:
            session_data = StateManager._sessions.get(session_id)
            if session_data:
                return {
                    "exists": True,
                    "session_id": session_id,
                    "current_agent": session_data.get("current_agent"),
                    "order_items": session_data.get("order_items", []),
                    "call_sid": session_data.get("call_sid"),
                    "conversation_history_length": len(session_data.get("conversation_history", [])),
                    "all_session_ids": list(StateManager._sessions.keys())[:5]  # First 5 sessions
                }
            else:
                return {
                    "exists": False, 
                    "session_id": session_id,
                    "all_session_ids": list(StateManager._sessions.keys())[:5]
                }
        except Exception as e:
            return {"error": str(e), "session_id": session_id}

    # These methods are simplified for in-memory version
    @staticmethod
    async def set_interrupt_flag(session_id: str, flag: bool):
        await StateManager.update_session(session_id, interrupt_flag=flag)

    @staticmethod
    async def get_interrupt_flag(session_id: str) -> bool:
        session_data = StateManager._sessions.get(session_id)
        return session_data.get("interrupt_flag", False) if session_data else False

    @staticmethod
    async def cleanup_expired_sessions():
        """Simple cleanup - remove sessions older than 1 hour"""
        try:
            now = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session_data in StateManager._sessions.items():
                last_activity = datetime.fromisoformat(session_data.get("last_activity", now.isoformat()))
                if now - last_activity > StateManager.SESSION_TTL:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await StateManager.end_session(session_id)
                
            if expired_sessions:
                logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired sessions: {e}")

    @staticmethod
    async def initialize():
        """Initialize the state manager"""
        logger.info("✅ StateManager initialized (IN-MEMORY MODE)")
        # Start background cleanup
        asyncio.create_task(_periodic_cleanup())


async def _periodic_cleanup():
    """Periodic cleanup of expired sessions"""
    while True:
        try:
            await StateManager.cleanup_expired_sessions()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"❌ Periodic cleanup error: {e}")
            await asyncio.sleep(300)