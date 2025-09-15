from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models.movie import Movie
from app.notifications.broadcaster import broadcaster
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MovieService:
    """Service class for movie management operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def get_all_movies(self) -> List[Dict[str, Any]]:
        """Get all movies in the catalog"""
        try:
            movies = self.db.query(Movie).all()
            return [
                {
                    "id": str(movie.id),
                    "title": movie.title,
                    "duration": movie.duration,
                    "genre": movie.genre,
                    "rating": movie.rating,
                    "description": movie.description,
                    "release_date": movie.release_date.isoformat() if movie.release_date else None,
                    "created_at": movie.created_at.isoformat(),
                    "updated_at": movie.updated_at.isoformat()
                }
                for movie in movies
            ]
        except Exception as e:
            logger.error(f"Error getting all movies: {e}")
            raise

    async def get_movie_by_id(self, movie_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific movie by ID"""
        try:
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                return None

            return {
                "id": str(movie.id),
                "title": movie.title,
                "duration": movie.duration,
                "genre": movie.genre,
                "rating": movie.rating,
                "description": movie.description,
                "release_date": movie.release_date.isoformat() if movie.release_date else None,
                "created_at": movie.created_at.isoformat(),
                "updated_at": movie.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting movie by ID {movie_id}: {e}")
            raise

    async def search_movies(
        self,
        title: str = None,
        genre: str = None,
        rating: str = None
    ) -> List[Dict[str, Any]]:
        """Search movies by various criteria"""
        try:
            query = self.db.query(Movie)

            filters = []
            if title:
                filters.append(Movie.title.ilike(f"%{title}%"))
            if genre:
                filters.append(Movie.genre.ilike(f"%{genre}%"))
            if rating:
                filters.append(Movie.rating == rating)

            if filters:
                query = query.filter(or_(*filters))

            movies = query.all()
            return [
                {
                    "id": str(movie.id),
                    "title": movie.title,
                    "duration": movie.duration,
                    "genre": movie.genre,
                    "rating": movie.rating,
                    "description": movie.description,
                    "release_date": movie.release_date.isoformat() if movie.release_date else None,
                    "created_at": movie.created_at.isoformat(),
                    "updated_at": movie.updated_at.isoformat()
                }
                for movie in movies
            ]
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            raise

    async def create_movie(
        self,
        title: str,
        duration: int,
        genre: str,
        rating: str,
        description: str,
        release_date: str = None
    ) -> Dict[str, Any]:
        """Create a new movie"""
        try:
            # Check if movie with same title already exists
            existing = self.db.query(Movie).filter(Movie.title.ilike(title)).first()
            if existing:
                raise ValueError(f"Movie with title '{title}' already exists")

            # Parse release date if provided
            parsed_release_date = None
            if release_date:
                try:
                    parsed_release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                except ValueError:
                    # Try alternative formats
                    try:
                        parsed_release_date = datetime.strptime(release_date, '%Y-%m-%d')
                    except ValueError:
                        raise ValueError(f"Invalid release date format: {release_date}")

            movie = Movie(
                title=title,
                duration=duration,
                genre=genre,
                rating=rating,
                description=description,
                release_date=parsed_release_date
            )

            self.db.add(movie)
            self.db.commit()
            self.db.refresh(movie)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="movies",
                operation="create",
                entity_id=str(movie.id),
                data={
                    "title": movie.title,
                    "genre": movie.genre,
                    "rating": movie.rating
                }
            )

            return {
                "id": str(movie.id),
                "title": movie.title,
                "duration": movie.duration,
                "genre": movie.genre,
                "rating": movie.rating,
                "description": movie.description,
                "release_date": movie.release_date.isoformat() if movie.release_date else None,
                "created_at": movie.created_at.isoformat(),
                "updated_at": movie.updated_at.isoformat(),
                "message": f"Movie '{title}' created successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating movie: {e}")
            raise

    async def update_movie(
        self,
        movie_id: str,
        title: str = None,
        duration: int = None,
        genre: str = None,
        rating: str = None,
        description: str = None,
        release_date: str = None
    ) -> Dict[str, Any]:
        """Update an existing movie"""
        try:
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                raise ValueError(f"Movie with ID {movie_id} not found")

            if title is not None:
                # Check for title conflicts with other movies
                existing = self.db.query(Movie).filter(
                    and_(Movie.title.ilike(title), Movie.id != movie_id)
                ).first()
                if existing:
                    raise ValueError(f"Another movie with title '{title}' already exists")
                movie.title = title

            if duration is not None:
                movie.duration = duration
            if genre is not None:
                movie.genre = genre
            if rating is not None:
                movie.rating = rating
            if description is not None:
                movie.description = description

            if release_date is not None:
                try:
                    parsed_release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        parsed_release_date = datetime.strptime(release_date, '%Y-%m-%d')
                    except ValueError:
                        raise ValueError(f"Invalid release date format: {release_date}")
                movie.release_date = parsed_release_date

            self.db.commit()
            self.db.refresh(movie)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="movies",
                operation="update",
                entity_id=movie_id,
                data={
                    "title": movie.title,
                    "genre": movie.genre,
                    "rating": movie.rating
                }
            )

            return {
                "id": str(movie.id),
                "title": movie.title,
                "duration": movie.duration,
                "genre": movie.genre,
                "rating": movie.rating,
                "description": movie.description,
                "release_date": movie.release_date.isoformat() if movie.release_date else None,
                "updated_at": movie.updated_at.isoformat(),
                "message": f"Movie '{movie.title}' updated successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating movie: {e}")
            raise

    async def delete_movie(self, movie_id: str) -> Dict[str, Any]:
        """Delete a movie (if no schedules exist)"""
        try:
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                raise ValueError(f"Movie with ID {movie_id} not found")

            # Check if movie has any schedules
            # This would require importing Schedule model, but avoiding circular imports
            # For now, we'll assume it's safe to delete
            # TODO: Add schedule check once schedule_service is implemented

            movie_title = movie.title
            self.db.delete(movie)
            self.db.commit()

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="movies",
                operation="delete",
                entity_id=movie_id,
                data={
                    "title": movie_title
                }
            )

            return {
                "id": movie_id,
                "message": f"Movie '{movie_title}' deleted successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting movie: {e}")
            raise

    async def get_movies_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Get all movies of a specific genre"""
        try:
            movies = self.db.query(Movie).filter(Movie.genre.ilike(f"%{genre}%")).all()
            return [
                {
                    "id": str(movie.id),
                    "title": movie.title,
                    "duration": movie.duration,
                    "genre": movie.genre,
                    "rating": movie.rating,
                    "description": movie.description,
                    "release_date": movie.release_date.isoformat() if movie.release_date else None
                }
                for movie in movies
            ]
        except Exception as e:
            logger.error(f"Error getting movies by genre {genre}: {e}")
            raise

    async def get_movie_statistics(self) -> Dict[str, Any]:
        """Get statistics about the movie catalog"""
        try:
            total_movies = self.db.query(Movie).count()

            # Get genre distribution
            genres = self.db.query(Movie.genre).distinct().all()
            genre_counts = {}
            for (genre,) in genres:
                count = self.db.query(Movie).filter(Movie.genre == genre).count()
                genre_counts[genre] = count

            # Get rating distribution
            ratings = self.db.query(Movie.rating).distinct().all()
            rating_counts = {}
            for (rating,) in ratings:
                count = self.db.query(Movie).filter(Movie.rating == rating).count()
                rating_counts[rating] = count

            return {
                "total_movies": total_movies,
                "genre_distribution": genre_counts,
                "rating_distribution": rating_counts,
                "available_genres": [genre for (genre,) in genres],
                "available_ratings": [rating for (rating,) in ratings]
            }
        except Exception as e:
            logger.error(f"Error getting movie statistics: {e}")
            raise

# Global movie service instance
movie_service = MovieService()