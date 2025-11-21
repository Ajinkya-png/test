from typing import Dict, List, Optional, Any
import logging
from ..core.database import SessionLocal
# from ..models.database import Driver, Order
import json
import uuid
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers using the Haversine formula."""
    R = 6371  # Earth radius in km

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


async def find_available_drivers(restaurant_location: Dict, radius_km: float = 5.0) -> List[Dict]:
    """Find available drivers near restaurant (mock or DB-backed)."""
    try:
        db = SessionLocal()
        # drivers = db.query(Driver).filter(Driver.is_available == True).all()
        # Mock drivers list for demonstration:
        mock_drivers = [
            {"id": "drv-1", "name": "Alice", "current_location": {"latitude": restaurant_location["latitude"] + 0.01, "longitude": restaurant_location["longitude"] + 0.01}, "is_available": True},
            {"id": "drv-2", "name": "Bob", "current_location": {"latitude": restaurant_location["latitude"] + 0.05, "longitude": restaurant_location["longitude"] + 0.02}, "is_available": True},
        ]

        available_drivers = []
        restaurant_lat = restaurant_location.get("latitude")
        restaurant_lon = restaurant_location.get("longitude")

        if restaurant_lat is None or restaurant_lon is None:
            logger.error("Invalid restaurant location")
            return []

        for driver in mock_drivers:
            if driver.get("current_location"):
                driver_lat = driver["current_location"].get("latitude")
                driver_lon = driver["current_location"].get("longitude")

                if driver_lat is not None and driver_lon is not None:
                    distance = calculate_distance(
                        restaurant_lat, restaurant_lon,
                        driver_lat, driver_lon
                    )

                    if distance <= radius_km:
                        available_drivers.append({
                            "driver_id": driver["id"],
                            "name": driver["name"],
                            "distance_km": round(distance, 2),
                            "location": driver["current_location"]
                        })

        return available_drivers
    except Exception as e:
        logger.error(f"Error finding available drivers: {e}")
        return []
    finally:
        try:
            db.close()
        except Exception:
            pass


async def assign_driver(order_id: str, driver_id: str) -> Dict[str, Any]:
    """Assign a driver to an order (mock)."""
    try:
        # In production: update Order.driver_id and notify driver via push/SMS
        return {
            "success": True,
            "order_id": order_id,
            "driver_id": driver_id,
            "message": f"Driver {driver_id} assigned to order {order_id}"
        }
    except Exception as e:
        logger.error(f"Error assigning driver: {e}")
        return {"error": "Failed to assign driver"}
