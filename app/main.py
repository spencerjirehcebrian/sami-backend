from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.websocket.manager import websocket_router
from app.api.movies import router as movies_router
from app.api.cinemas import router as cinemas_router
from app.api.schedules import router as schedules_router
from app.api.analytics import router as analytics_router
from app.notifications.events import setup_database_event_handlers

app = FastAPI(title="SAMi Backend API", version="1.0.0", description="Cinema Schedule Management AI Backend")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
app.include_router(analytics_router)

# Setup database event handlers for notifications
setup_database_event_handlers()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "SAMi Backend API"
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