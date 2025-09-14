from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="SAMi Backend API", version="1.0.0", description="Cinema Schedule Management AI Backend")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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