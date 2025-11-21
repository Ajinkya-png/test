from typing import Dict, List, Optional, Any
import logging
from ..core.database import SessionLocal
# Models are referenced but not implemented here; imports left as-is.
# from ..models.database import Customer, Restaurant, MenuItem, Order
import json
import uuid

logger = logging.getLogger(__name__)


# NOTE: The following implementations assume SQLAlchemy models (Customer, MenuItem, Order).
# If running locally without models, these functions will need to be adapted or mocked.


async def get_customer_profile(phone_number: str) -> Dict[str, Any]:
    """Get customer profile by phone number or create a minimal profile if none exists."""
    try:
        db = SessionLocal()
        # Example: query Customer model (commented because models may be missing)
        # customer = db.query(Customer).filter(Customer.phone_number == phone_number).first()
        customer = None  # placeholder for runtime without models

        if customer:
            return {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone_number": customer.phone_number,
                "addresses": [
                    {
                        "id": addr.id,
                        "address_line1": addr.address_line1,
                        "city": addr.city,
                        "state": addr.state,
                        "zip_code": addr.zip_code,
                        "is_primary": addr.is_primary
                    }
                    for addr in customer.addresses
                ],
                "order_history": [
                    {
                        "id": order.id,
                        "restaurant_name": order.restaurant.name,
                        "total_amount": order.total_amount,
                        "status": order.status,
                        "created_at": order.created_at.isoformat()
                    }
                    for order in customer.orders.order_by()[:5]
                ]
            }
        else:
            # Create new minimal profile
            new_customer = {
                "id": str(uuid.uuid4()),
                "phone_number": phone_number,
                "is_new_customer": True
            }
            return new_customer

    except Exception as e:
        logger.error(f"Error getting customer profile: {e}")
        return {"error": "Failed to retrieve customer profile"}
    finally:
        try:
            db.close()
        except Exception:
            pass


async def search_menu(restaurant_id: str = None, query: str = "", filters: Dict = None) -> List[Dict]:
    """Search menu items with optional filters. Returns simplified results when DB models are absent."""
    try:
        # If DB models exist, perform real query. Here we return mocked example results.
        sample_item = {
            "id": "item-1",
            "name": "Margherita Pizza",
            "description": "Classic pizza with tomato sauce and mozzarella",
            "price": 9.99,
            "category": "pizza",
            "dietary_info": {"vegetarian": True},
            "customizations": {"extra_cheese": True}
        }
        return [sample_item]
    except Exception as e:
        logger.error(f"Error searching menu: {e}")
        return []


async def get_item_details(item_id: str) -> Dict[str, Any]:
    """Return details for an item (mocked if DB not available)."""
    try:
        # Placeholder example
        return {
            "id": item_id,
            "name": "Example Item",
            "description": "Detailed description",
            "price": 7.5,
            "category": "example",
            "dietary_info": {},
            "customizations": {}
        }
    except Exception as e:
        logger.error(f"Error getting item details: {e}")
        return {"error": "Failed to retrieve item details"}


async def add_to_order(item_id: str, quantity: int = 1, customizations: Dict = None, session_data: Dict = None) -> Dict[str, Any]:
    """Add item to session_data['order_items'] (in-memory session)."""
    try:
        # Get item info (mock)
        item = {
            "id": item_id,
            "name": "Sample Item",
            "price": 9.99,
            "restaurant_id": session_data.get("restaurant_id") if session_data else None,
            "is_available": True,
            "category": "default",
            "customizations": customizations or {}
        }

        if not item["is_available"]:
            return {"error": "Item is currently unavailable"}

        order_item = {
            "item_id": item_id,
            "name": item["name"],
            "price": item["price"],
            "quantity": quantity,
            "customizations": customizations or {},
            "subtotal": round(item["price"] * quantity, 2)
        }

        if session_data is not None:
            session_data.setdefault("order_items", [])
            session_data.setdefault("restaurant_id", item.get("restaurant_id"))
            session_data["order_items"].append(order_item)

        return {
            "success": True,
            "item": order_item,
            "message": f"Added {quantity}x {item['name']} to order"
        }
    except Exception as e:
        logger.error(f"Error adding to order: {e}")
        return {"error": "Failed to add item to order"}


async def remove_from_order(item_id: str, session_data: Dict = None) -> Dict[str, Any]:
    """Remove an item from the in-memory order in session_data."""
    try:
        if not session_data or "order_items" not in session_data:
            return {"error": "No items in order"}

        for i, item in enumerate(session_data["order_items"]):
            if item.get("item_id") == item_id:
                removed_item = session_data["order_items"].pop(i)
                return {
                    "success": True,
                    "removed_item": removed_item,
                    "message": f"Removed {removed_item['name']} from order"
                }

        return {"error": "Item not found in order"}
    except Exception as e:
        logger.error(f"Error removing from order: {e}")
        return {"error": "Failed to remove item from order"}


async def calculate_total(session_data: Dict = None, apply_promotions: bool = False) -> Dict[str, Any]:
    """Calculate subtotal, fees, tax and total for the current in-memory order."""
    try:
        if not session_data or "order_items" not in session_data or not session_data["order_items"]:
            return {"error": "No items in order"}

        subtotal = sum(item.get("subtotal", 0.0) for item in session_data["order_items"])

        # Simplified fees
        delivery_fee = 5.0 if subtotal < 25 else 0.0
        service_fee = subtotal * 0.1
        tax = subtotal * 0.08

        total = subtotal + delivery_fee + service_fee + tax

        return {
            "subtotal": round(subtotal, 2),
            "delivery_fee": round(delivery_fee, 2),
            "service_fee": round(service_fee, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "currency": "USD"
        }
    except Exception as e:
        logger.error(f"Error calculating total: {e}")
        return {"error": "Failed to calculate order total"}


async def verify_address(address: str) -> Dict[str, Any]:
    """Mock address verification; in production you'd call Google Maps or similar."""
    try:
        address_lower = address.lower()
        if any(word in address_lower for word in ["123 main", "456 oak", "789 pine"]):
            return {
                "verified": True,
                "standardized_address": address.title(),
                "zone": "deliverable",
                "estimated_delivery_time": "30-45 minutes"
            }
        else:
            return {
                "verified": False,
                "error": "Address not in delivery area",
                "suggestion": "Please check your address or contact support"
            }
    except Exception as e:
        logger.error(f"Error verifying address: {e}")
        return {"error": "Failed to verify address"}


async def place_order(payment_method_id: str, session_data: Dict = None) -> Dict[str, Any]:
    """Place the final order (mock). In production this writes to DB and charges payment."""
    try:
        if not session_data:
            return {"error": "No session data"}

        if "order_items" not in session_data or not session_data["order_items"]:
            return {"error": "No items in order"}

        if "customer_id" not in session_data:
            # minimal check: require customer identification
            return {"error": "Customer not identified"}

        if "delivery_address" not in session_data:
            return {"error": "Delivery address not set"}

        # Compute totals
        total_result = await calculate_total(session_data)
        if "error" in total_result:
            return total_result

        # Create a mock order object
        order_id = str(uuid.uuid4())
        # In a real system, save to DB using models.Order
        session_data["order_items"] = []
        session_data["current_order_id"] = order_id

        return {
            "success": True,
            "order_id": order_id,
            "total_amount": total_result["total"],
            "estimated_delivery_time": "30-45 minutes",
            "confirmation_number": order_id[:8].upper()
        }
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return {"error": "Failed to place order"}
