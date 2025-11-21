import logging
from typing import Dict, Any
from ..tools.driver_tools import calculate_distance
from .maps_service import MapsService

logger = logging.getLogger(__name__)


class TrackingService:
    """
    Tracking helpers to compute ETA and process location updates.
    Uses Google Maps API when available, falls back to local math.
    """

    @staticmethod
    def compute_eta(distance_km: float, avg_speed_kmph: float = 30.0) -> int:
        if avg_speed_kmph <= 0:
            return 999
        hours = distance_km / avg_speed_kmph
        minutes = int(hours * 60)
        return max(1, minutes)

    @staticmethod
    def eta_from_coords(lat1, lon1, lat2, lon2) -> Dict[str, Any]:
        """
        Compute distance and ETA between two coordinates.
        Fallback: offline calculation
        """
        try:
            maps = MapsService()
            result = maps.calculate_eta(
                origin=(lat1, lon1),
                destination=(lat2, lon2)
            )
            if result:
                return {
                    "distance_km": result["distance_km"],
                    "eta_min": result["duration_min"],
                    "source": "google_maps"
                }
        except Exception as e:
            logger.warning(f"[TrackingService] Google Maps ETA failed: {e}")

        # fallback to offline Haversine
        distance = calculate_distance(lat1, lon1, lat2, lon2)
        eta = TrackingService.compute_eta(distance)
        return {
            "distance_km": round(distance, 2),
            "eta_min": eta,
            "source": "local_fallback"
        }
