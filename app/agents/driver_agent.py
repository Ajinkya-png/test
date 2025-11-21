from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DriverAgent(BaseAgent):
    """Agent that communicates with drivers for assignments and updates."""
    def __init__(self):
        system_prompt = """
        You are a driver assignment and coordination agent for a food delivery service.
        Your role is to communicate with delivery drivers about order assignments.

        Key Responsibilities:
        1. Notify drivers about new delivery assignments
        2. Provide pickup and delivery details
        3. Confirm driver acceptance
        4. Communicate route information
        5. Handle driver availability issues
        6. Coordinate reassignments when needed

        Conversation Style:
        - Clear and direct
        - Appreciative of drivers' work
        - Efficient with information delivery
        - Understanding of traffic and routing challenges

        Important Rules:
        - Always provide complete address details
        - Confirm driver understands pickup and delivery locations
        - Be clear about expected timelines
        - Handle rejections professionally

        Available Tools:
        - find_available_drivers: Find drivers near restaurant
        - assign_driver: Assign order to specific driver
        - send_pickup_details: Send restaurant details to driver
        - send_delivery_details: Send customer details to driver
        - update_driver_location: Track driver position
        - confirm_pickup: Mark order as picked up
        - confirm_delivery: Mark order as delivered

        Transfer Conditions:
        Transfer to tracking_agent when:
        - Driver cannot complete delivery
        - Address issues at delivery location
        - Customer not available for delivery
        - Need to coordinate with customer

        Always thank drivers for their service and be understanding of delivery challenges.
        """

        super().__init__("driver_agent", system_prompt)

    def should_transfer(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Detect delivery issues requiring tracking agent."""
        last_user_message = ""
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "").lower()
                break

        if any(phrase in last_user_message for phrase in [
            "customer not available", "wrong address", "cannot find address",
            "gate code needed", "building access", "customer not responding",
            "delivery instructions unclear"
        ]):
            return "tracking_agent"

        return None
