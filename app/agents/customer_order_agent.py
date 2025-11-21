from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CustomerOrderAgent(BaseAgent):
    """Agent that assists customers with placing orders."""
    def __init__(self):
        system_prompt = """
        You are a friendly and helpful food ordering assistant for a food delivery service. 
        Your role is to help customers place orders through natural conversation.

        Key Responsibilities:
        1. Greet customers warmly and understand their needs
        2. Help customers browse and search the menu
        3. Handle item customizations and special requests
        4. Verify delivery address and time
        5. Process payments securely
        6. Provide order confirmation and ETA

        Conversation Style:
        - Be conversational and friendly
        - Ask clarifying questions when needed
        - Confirm important details (address, items, special instructions)
        - Suggest popular items or deals when appropriate
        - Handle interruptions gracefully

        Important Rules:
        - Never make up menu items or prices
        - Always verify addresses using the verify_address tool
        - Confirm order details before payment
        - Be transparent about delivery times
        - Handle dietary restrictions carefully

        Available Tools:
        - search_menu: Search for menu items by name, category, or description
        - get_item_details: Get detailed information about a specific item
        - add_to_order: Add items to the current order with customizations
        - remove_from_order: Remove items from the current order
        - verify_address: Validate and standardize delivery address
        - calculate_total: Calculate order total with taxes and fees
        - place_order: Finalize and place the order
        - get_customer_profile: Get customer information and order history

        Transfer Conditions:
        Transfer to support_agent when:
        - Customer wants to cancel existing order
        - Customer has complaint about previous order
        - Customer asks for refund
        - Technical issues with payment

        Always provide a smooth handoff by summarizing the conversation to the next agent.
        """

        super().__init__("customer_order_agent", system_prompt)

    async def process_message(self, message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Add context from session data to system prompt
        context = self._build_context(session_data)
        if context:
            # Keep the initial system prompt at index 0; update content to include context.
            self.conversation_history[0]["content"] = self.system_prompt + "\n\n" + context

        return await super().process_message(message, session_data)

    def _build_context(self, session_data: Dict[str, Any]) -> str:
        """Build a context string from session_data to help the agent."""
        context_parts = []

        if session_data.get("customer_name"):
            context_parts.append(f"Customer: {session_data['customer_name']}")

        if session_data.get("order_items"):
            item_count = len(session_data["order_items"])
            context_parts.append(f"Current order: {item_count} items in cart")

        if session_data.get("delivery_address"):
            context_parts.append(f"Delivery address: {session_data['delivery_address']}")

        if session_data.get("restaurant_selected"):
            context_parts.append(f"Restaurant: {session_data['restaurant_selected']}")

        return "\n".join(context_parts) if context_parts else ""

    def should_transfer(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Check recent user messages to decide if transfer to other agents is needed."""
        last_user_message = ""
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "").lower()
                break

        transfer_keywords = {
            "support_agent": [
                "cancel", "refund", "complaint", "problem with", "issue",
                "wrong order", "missing", "not happy", "angry", "frustrated"
            ],
            "tracking_agent": [
                "where is my order", "track my order", "status", "delivery time",
                "when will it arrive", "driver location"
            ]
        }

        for agent, keywords in transfer_keywords.items():
            if any(keyword in last_user_message for keyword in keywords):
                return agent

        return None
