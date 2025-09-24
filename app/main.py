from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.websocket.manager import websocket_router
from app.api.movies import router as movies_router
from app.api.cinemas import router as cinemas_router
from app.api.schedules import router as schedules_router
from app.api.forecasts import router as forecasts_router
from app.api.chat import router as chat_router
from app.notifications.events import setup_database_event_handlers
from app.database import test_db_connection, get_db_health
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SAMi Backend API...")
    await test_db_connection()
    yield
    # Shutdown
    logger.info("Shutting down SAMi Backend API...")


app = FastAPI(
    title="SAMi Backend API",
    version="1.0.0",
    description="Cinema Schedule Management AI Backend",
    lifespan=lifespan
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router
app.include_router(websocket_router)

# Include REST API routers
app.include_router(movies_router)
app.include_router(cinemas_router)
app.include_router(schedules_router)
app.include_router(forecasts_router)
app.include_router(chat_router)

# Setup database event handlers for notifications
setup_database_event_handlers()

# Health check endpoint
@app.get("/health")
async def health_check():
    db_health = get_db_health()
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"

    return {
        "status": overall_status,
        "version": "1.0.0",
        "service": "SAMi Backend API",
        "database": db_health
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "SAMi Backend API",
        "description": "FastAPI backend for cinema schedule management with AI integration",
        "health": "/health",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)