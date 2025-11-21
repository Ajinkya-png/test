"""
Helpers to expose Prometheus metrics using the prometheus_client library.
If you add `prometheus_client`, you can use this to register counters/gauges.
"""

from prometheus_client import Counter, Gauge, Histogram
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Example metrics
CALLS_TOTAL = Counter("food_delivery_calls_total", "Total number of calls")
CALL_DURATION = Histogram("food_delivery_call_duration_seconds", "Call duration histogram")
ONLINE_DRIVERS = Gauge("food_delivery_online_drivers", "Number of available drivers")


def register_metrics(app: FastAPI):
    """
    Attach /metrics Prometheus endpoint to FastAPI.
    """
    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
