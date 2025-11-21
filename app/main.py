"""
Main entry point for the Food Delivery Voice AI system.

Creates the FastAPI app, registers routers, middleware,
and initializes monitoring endpoints, databases, and agents.
"""

# import logging
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from prometheus_fastapi_instrumentator import Instrumentator
# from fastapi.routing import APIRoute
# from app.routers.voice import router as voice_router


# from .core.config import settings
# from .routers import (
#     orders,
#     voice,
#     agents,
#     analytics,
#     monitoring,
# )
# from .monitoring.prometheus_metrics import register_metrics


# from app.core.config import settings
# print("🚨 ACTUALLY LOADED PUBLIC_BASE_URL =", settings.PUBLIC_BASE_URL)


# # ------------------------------------------------------------
# # APP INITIALIZATION
# # ------------------------------------------------------------
# app = FastAPI(
#     title="Food Delivery Voice AI",
#     version="1.0.0",
#     description="Multi-Agent Voice Calling System for Food Delivery",
#     contact={"email": "support@voiceai.io"},
# )

# logger = logging.getLogger(__name__)
# logger.info("🚀 Starting Food Delivery Voice AI backend...")

# # ------------------------------------------------------------
# # PROMETHEUS MUST BE ADDED *BEFORE* STARTUP
# # ------------------------------------------------------------
# # Adds middleware immediately (valid)
# Instrumentator().instrument(app).expose(app)

# # Adds /metrics endpoint
# register_metrics(app)

# # ------------------------------------------------------------
# # STARTUP EVENT
# # ------------------------------------------------------------
# @app.on_event("startup")
# async def startup_event():
#     """Initialize resources on startup."""
#     logger.info("📦 Database initialized.")
#     logger.info("📊 Prometheus metrics ready.")
#     logger.info(f"✅ Environment: {settings.ENVIRONMENT}")

# # ------------------------------------------------------------
# # CORS CONFIGURATION
# # ------------------------------------------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ------------------------------------------------------------
# # ROUTERS REGISTRATION
# # ------------------------------------------------------------
# app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
# app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
# app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])

# # ------------------------------------------------------------
# # ROOT ENDPOINT
# # ------------------------------------------------------------
# @app.get("/", tags=["Root"])
# async def root():
#     """Basic health check."""
#     return {
#         "message": "Food Delivery Voice AI backend running successfully.",
#         "environment": settings.ENVIRONMENT,
#     }

# # ------------------------------------------------------------
# # SHUTDOWN EVENT
# # ------------------------------------------------------------
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("🛑 Shutting down Food Delivery Voice AI system...")


# print("📌 REGISTERED ROUTES:")
# for route in app.routes:
#     if hasattr(route, "methods"):
#         print("➡️", route.path, route.methods)
#     else:
#         print("➡️", route.path, "WEBSOCKET")


# # ------------------------------------------------------------
# # ENTRY POINT
# # ------------------------------------------------------------
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=settings.DEBUG_MODE,
#     )

# # ROOT ENDPOINT
# @app.get("/", tags=["Root"])
# async def root():
#     """Basic health check."""
#     return {
#         "message": "Food Delivery Voice AI backend running successfully.",
#         "environment": settings.ENVIRONMENT,
#     }

# # FAVICON (prevent browser 404)
# from fastapi.responses import Response

# @app.get("/favicon.ico")
# async def favicon():
#     return Response(status_code=204)

"""
Main entry point for the Food Delivery Voice AI system.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.orchestration.state_manager import StateManager
from app.routers import orders, voice, agents, analytics, monitoring
from app.monitoring.prometheus_metrics import register_metrics

print("🚨 ACTUALLY LOADED PUBLIC_BASE_URL =", settings.PUBLIC_BASE_URL)

# ------------------------------------------------------------
# APP INITIALIZATION
# ------------------------------------------------------------
app = FastAPI(
    title="Food Delivery Voice AI",
    version="1.0.0",
    description="Multi-Agent Voice Calling System for Food Delivery",
)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting Food Delivery Voice AI backend...")

# ------------------------------------------------------------
# PROMETHEUS
# ------------------------------------------------------------
Instrumentator().instrument(app).expose(app)
register_metrics(app)

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("📦 Database initialized.")
    logger.info("📊 Prometheus metrics ready.")
    logger.info(f"✅ Environment: {settings.ENVIRONMENT}")

# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# ROUTERS
# ------------------------------------------------------------
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])

# ------------------------------------------------------------
# ROOT ENDPOINT (ONLY ONCE)
# ------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Food Delivery Voice AI backend running successfully.",
        "environment": settings.ENVIRONMENT,
    }

# ------------------------------------------------------------
# FAVICON
# ------------------------------------------------------------
from fastapi.responses import Response

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


print("📌 REGISTERED ROUTES:")
for route in app.routes:
    if hasattr(route, "methods"):
        print("➡️", route.path, route.methods)
    else:
        print("➡️", route.path, "WEBSOCKET")

@app.on_event("startup")
async def startup_event():
    # Initialize StateManager
    await StateManager.initialize()
    logger.info("✅ StateManager initialized")
    
    logger.info("📦 Database initialized.")
    logger.info("📊 Prometheus metrics ready.")
    logger.info(f"✅ Environment: {settings.ENVIRONMENT}")
