# Router package initializer
from .voice import router as voice_router
from .agents import router as agents_router
from .analytics import router as analytics_router
from .monitoring import router as monitoring_router
from .orders import router as orders_router

__all__ = [
    "voice_router",
    "agents_router",
    "analytics_router",
    "monitoring_router",
    "orders_router",
]
