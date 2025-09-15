# SAMi Backend API

FastAPI backend for cinema schedule management system with AI-powered natural language processing.

## Features

- FastAPI web framework with WebSocket support
- PostgreSQL database with SQLAlchemy ORM
- Google Gemini AI integration for natural language processing
- Real-time chat interface for schedule management
- Comprehensive analytics and optimization services

## Setup

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Set up environment variables in `.env`:

   ```
   DATABASE_URL=postgresql://user:pass@host:port/db
   GEMINI_API_KEY=your_api_key
   CORS_ORIGINS=["http://localhost:3000"]
   ```

3. Run database migrations:

   ```bash
   poetry run alembic upgrade head
   poetry run python alembic/seed.py
   ```

4. Start the server:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## API Endpoints

- `GET /health` - Health check endpoint
- `WS /ws/{session_id}` - WebSocket endpoint for chat

## Architecture

- **Models**: SQLAlchemy database models
- **Services**: Business logic layer
- **Gemini**: AI integration and function calling
- **WebSocket**: Real-time communication handling
