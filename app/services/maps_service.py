"""
app/services/maps_service.py

Google Maps Service for Food Delivery Voice AI
------------------------------------------------
Handles:
✅ Address verification & normalization
✅ Reverse geocoding (lat/lon → address)
✅ ETA & distance calculations using live data
✅ Route optimization for drivers

Requires:
- GOOGLE_MAPS_API_KEY in .env
"""

import googlemaps
from typing import Tuple, Dict, List, Optional
from datetime import datetime
from app.core.config import settings


class MapsService:
    """
    Service for interacting with Google Maps APIs.
    """

    def __init__(self):
        try:
            self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        except Exception as e:
            raise RuntimeError(f"[MapsService] Failed to initialize: {e}")

    # ----------------------------------------------------------
    # Address Verification (Geocoding)
    # ----------------------------------------------------------
    def verify_address(self, address: str) -> Optional[Dict]:
        """
        Verify and normalize a customer-provided address string.

        Returns:
            dict with formatted_address, latitude, longitude
        """
        try:
            results = self.client.geocode(address)
            if not results:
                return None

            loc = results[0]["geometry"]["location"]
            return {
                "formatted_address": results[0]["formatted_address"],
                "latitude": loc["lat"],
                "longitude": loc["lng"],
            }
        except Exception as e:
            print(f"[MapsService] Address verification failed: {e}")
            return None

    # ----------------------------------------------------------
    # Reverse Geocoding
    # ----------------------------------------------------------
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates into a human-readable address.
        """
        try:
            results = self.client.reverse_geocode((lat, lng))
            if results:
                return results[0]["formatted_address"]
        except Exception as e:
            print(f"[MapsService] Reverse geocode failed: {e}")
        return None

    # ----------------------------------------------------------
    # Distance & ETA Calculation
    # ----------------------------------------------------------
    def calculate_eta(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "driving",
    ) -> Optional[Dict]:
        """
        Compute distance and ETA using live Google Maps data.

        Args:
            origin: (lat, lon)
            destination: (lat, lon)
            mode: driving | walking | bicycling

        Returns:
            dict with distance_km, duration_min, text_summary
        """
        try:
            matrix = self.client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode=mode,
                departure_time=datetime.now(),
            )

            element = matrix["rows"][0]["elements"][0]
            if element["status"] != "OK":
                return None

            distance_m = element["distance"]["value"]
            duration_s = element["duration"]["value"]

            return {
                "distance_km": round(distance_m / 1000, 2),
                "duration_min": round(duration_s / 60, 1),
                "text_summary": element["duration"]["text"],
            }

        except Exception as e:
            print(f"[MapsService] ETA calculation failed: {e}")
            return None

    # ----------------------------------------------------------
    # Route Optimization
    # ----------------------------------------------------------
    def get_optimal_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None,
    ) -> Optional[Dict]:
        """
        Returns the optimal route and summary info.
        """
        try:
            directions = self.client.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                mode="driving",
                optimize_waypoints=True,
                departure_time=datetime.now(),
            )

            if not directions:
                return None

            leg = directions[0]["legs"][0]
            distance_m = leg["distance"]["value"]
            duration_s = leg["duration"]["value"]

            return {
                "distance_km": round(distance_m / 1000, 2),
                "duration_min": round(duration_s / 60, 1),
                "polyline": directions[0]["overview_polyline"]["points"],
            }

        except Exception as e:
            print(f"[MapsService] Route optimization failed: {e}")
            return None
