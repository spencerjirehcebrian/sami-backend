from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.movie_service import MovieService
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/movies", tags=["movies"])

class MovieCreate(BaseModel):
    title: str
    duration: int
    genre: str
    rating: str
    description: Optional[str] = None
    release_date: Optional[str] = None

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    duration: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[str] = None

@router.get("/", response_model=List[Dict[str, Any]])
async def get_movies(
    genre: Optional[str] = Query(None, description="Filter by genre"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    db: Session = Depends(get_db)
):
    """Get all movies with optional filtering"""
    try:
        movie_service = MovieService(db)

        if genre or rating:
            # Use search functionality for filtering
            search_params = {}
            if genre:
                search_params["genre"] = genre
            if rating:
                search_params["rating"] = rating
            return await movie_service.search_movies(**search_params)
        else:
            return await movie_service.get_all_movies()
    except Exception as e:
        logger.error(f"Error getting movies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{movie_id}", response_model=Dict[str, Any])
async def get_movie(movie_id: str, db: Session = Depends(get_db)):
    """Get a specific movie by ID"""
    try:
        movie_service = MovieService(db)
        movie = await movie_service.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting movie {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=Dict[str, Any])
async def create_movie(movie_data: MovieCreate, db: Session = Depends(get_db)):
    """Create a new movie"""
    try:
        movie_service = MovieService(db)
        movie_dict = movie_data.dict(exclude_unset=True)
        return await movie_service.create_movie(**movie_dict)
    except Exception as e:
        logger.error(f"Error creating movie: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{movie_id}", response_model=Dict[str, Any])
async def update_movie(
    movie_id: str,
    movie_data: MovieUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing movie"""
    try:
        movie_service = MovieService(db)

        # Check if movie exists
        existing_movie = await movie_service.get_movie_by_id(movie_id)
        if not existing_movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Update with only provided fields
        update_dict = movie_data.dict(exclude_unset=True)
        return await movie_service.update_movie(movie_id, **update_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating movie {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{movie_id}")
async def delete_movie(movie_id: str, db: Session = Depends(get_db)):
    """Delete a movie"""
    try:
        movie_service = MovieService(db)

        # Check if movie exists
        existing_movie = await movie_service.get_movie_by_id(movie_id)
        if not existing_movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        await movie_service.delete_movie(movie_id)
        return {"message": "Movie deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting movie {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/performance", response_model=Dict[str, Any])
async def get_movie_performance(db: Session = Depends(get_db)):
    """Get movie performance statistics"""
    try:
        movie_service = MovieService(db)
        return await movie_service.get_movie_statistics()
    except Exception as e:
        logger.error(f"Error getting movie performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search/by-genre/{genre}", response_model=List[Dict[str, Any]])
async def get_movies_by_genre(genre: str, db: Session = Depends(get_db)):
    """Get movies filtered by genre"""
    try:
        movie_service = MovieService(db)
        return await movie_service.get_movies_by_genre(genre)
    except Exception as e:
        logger.error(f"Error getting movies by genre {genre}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")