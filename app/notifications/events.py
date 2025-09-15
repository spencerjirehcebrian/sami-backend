import asyncio
import logging
from sqlalchemy import event
from app.models.movie import Movie
from app.models.cinema import Cinema
from app.models.schedule import Schedule

logger = logging.getLogger(__name__)

def setup_database_event_handlers():
    """Set up SQLAlchemy event handlers for database change notifications"""

    # Movie event handlers
    @event.listens_for(Movie, 'after_insert')
    def movie_created(mapper, connection, target):
        """Handle movie creation events"""
        try:
            from app.notifications.broadcaster import broadcaster

            # Run the async function in the current event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, schedule the coroutine
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="movies",
                        operation="create",
                        entity_id=str(target.id),
                        data={
                            "title": target.title,
                            "genre": target.genre,
                            "rating": target.rating
                        }
                    ))
                else:
                    # If not in async context, run until complete
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="movies",
                        operation="create",
                        entity_id=str(target.id),
                        data={
                            "title": target.title,
                            "genre": target.genre,
                            "rating": target.rating
                        }
                    ))
            except RuntimeError:
                # Create new event loop if none exists
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="movies",
                    operation="create",
                    entity_id=str(target.id),
                    data={
                        "title": target.title,
                        "genre": target.genre,
                        "rating": target.rating
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in movie_created event handler: {e}")

    @event.listens_for(Movie, 'after_update')
    def movie_updated(mapper, connection, target):
        """Handle movie update events"""
        try:
            from app.notifications.broadcaster import broadcaster

            # Run the async function in the current event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="movies",
                        operation="update",
                        entity_id=str(target.id),
                        data={
                            "title": target.title,
                            "genre": target.genre,
                            "rating": target.rating
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="movies",
                        operation="update",
                        entity_id=str(target.id),
                        data={
                            "title": target.title,
                            "genre": target.genre,
                            "rating": target.rating
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="movies",
                    operation="update",
                    entity_id=str(target.id),
                    data={
                        "title": target.title,
                        "genre": target.genre,
                        "rating": target.rating
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in movie_updated event handler: {e}")

    @event.listens_for(Movie, 'after_delete')
    def movie_deleted(mapper, connection, target):
        """Handle movie deletion events"""
        try:
            from app.notifications.broadcaster import broadcaster

            # Run the async function in the current event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="movies",
                        operation="delete",
                        entity_id=str(target.id),
                        data={
                            "title": target.title
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="movies",
                        operation="delete",
                        entity_id=str(target.id),
                        data={
                            "title": target.title
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="movies",
                    operation="delete",
                    entity_id=str(target.id),
                    data={
                        "title": target.title
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in movie_deleted event handler: {e}")

    # Cinema event handlers
    @event.listens_for(Cinema, 'after_insert')
    def cinema_created(mapper, connection, target):
        """Handle cinema creation events"""
        try:
            from app.notifications.broadcaster import broadcaster

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="cinemas",
                        operation="create",
                        entity_id=str(target.id),
                        data={
                            "number": target.number,
                            "total_seats": target.total_seats,
                            "location": target.location
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="cinemas",
                        operation="create",
                        entity_id=str(target.id),
                        data={
                            "number": target.number,
                            "total_seats": target.total_seats,
                            "location": target.location
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="cinemas",
                    operation="create",
                    entity_id=str(target.id),
                    data={
                        "number": target.number,
                        "total_seats": target.total_seats,
                        "location": target.location
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in cinema_created event handler: {e}")

    @event.listens_for(Cinema, 'after_update')
    def cinema_updated(mapper, connection, target):
        """Handle cinema update events"""
        try:
            from app.notifications.broadcaster import broadcaster

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="cinemas",
                        operation="update",
                        entity_id=str(target.id),
                        data={
                            "number": target.number,
                            "total_seats": target.total_seats,
                            "location": target.location
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="cinemas",
                        operation="update",
                        entity_id=str(target.id),
                        data={
                            "number": target.number,
                            "total_seats": target.total_seats,
                            "location": target.location
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="cinemas",
                    operation="update",
                    entity_id=str(target.id),
                    data={
                        "number": target.number,
                        "total_seats": target.total_seats,
                        "location": target.location
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in cinema_updated event handler: {e}")

    @event.listens_for(Cinema, 'after_delete')
    def cinema_deleted(mapper, connection, target):
        """Handle cinema deletion events"""
        try:
            from app.notifications.broadcaster import broadcaster

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="cinemas",
                        operation="delete",
                        entity_id=str(target.id),
                        data={
                            "number": target.number
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="cinemas",
                        operation="delete",
                        entity_id=str(target.id),
                        data={
                            "number": target.number
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="cinemas",
                    operation="delete",
                    entity_id=str(target.id),
                    data={
                        "number": target.number
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in cinema_deleted event handler: {e}")

    # Schedule event handlers
    @event.listens_for(Schedule, 'after_insert')
    def schedule_created(mapper, connection, target):
        """Handle schedule creation events"""
        try:
            from app.notifications.broadcaster import broadcaster

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="schedules",
                        operation="create",
                        entity_id=str(target.id),
                        data={
                            "movie_id": str(target.movie_id),
                            "cinema_number": target.cinema_number,
                            "time_slot": target.time_slot.isoformat() if target.time_slot else None,
                            "price": float(target.price) if target.price else None
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="schedules",
                        operation="create",
                        entity_id=str(target.id),
                        data={
                            "movie_id": str(target.movie_id),
                            "cinema_number": target.cinema_number,
                            "time_slot": target.time_slot.isoformat() if target.time_slot else None,
                            "price": float(target.price) if target.price else None
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="schedules",
                    operation="create",
                    entity_id=str(target.id),
                    data={
                        "movie_id": str(target.movie_id),
                        "cinema_number": target.cinema_number,
                        "time_slot": target.time_slot.isoformat() if target.time_slot else None,
                        "price": float(target.price) if target.price else None
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in schedule_created event handler: {e}")

    @event.listens_for(Schedule, 'after_update')
    def schedule_updated(mapper, connection, target):
        """Handle schedule update events"""
        try:
            from app.notifications.broadcaster import broadcaster

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="schedules",
                        operation="update",
                        entity_id=str(target.id),
                        data={
                            "movie_id": str(target.movie_id),
                            "cinema_number": target.cinema_number,
                            "time_slot": target.time_slot.isoformat() if target.time_slot else None,
                            "price": float(target.price) if target.price else None
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="schedules",
                        operation="update",
                        entity_id=str(target.id),
                        data={
                            "movie_id": str(target.movie_id),
                            "cinema_number": target.cinema_number,
                            "time_slot": target.time_slot.isoformat() if target.time_slot else None,
                            "price": float(target.price) if target.price else None
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="schedules",
                    operation="update",
                    entity_id=str(target.id),
                    data={
                        "movie_id": str(target.movie_id),
                        "cinema_number": target.cinema_number,
                        "time_slot": target.time_slot.isoformat() if target.time_slot else None,
                        "price": float(target.price) if target.price else None
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in schedule_updated event handler: {e}")

    @event.listens_for(Schedule, 'after_delete')
    def schedule_deleted(mapper, connection, target):
        """Handle schedule deletion events"""
        try:
            from app.notifications.broadcaster import broadcaster

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcaster.broadcast_change(
                        entity_type="schedules",
                        operation="delete",
                        entity_id=str(target.id),
                        data={
                            "cinema_number": target.cinema_number,
                            "time_slot": target.time_slot.isoformat() if target.time_slot else None
                        }
                    ))
                else:
                    loop.run_until_complete(broadcaster.broadcast_change(
                        entity_type="schedules",
                        operation="delete",
                        entity_id=str(target.id),
                        data={
                            "cinema_number": target.cinema_number,
                            "time_slot": target.time_slot.isoformat() if target.time_slot else None
                        }
                    ))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcaster.broadcast_change(
                    entity_type="schedules",
                    operation="delete",
                    entity_id=str(target.id),
                    data={
                        "cinema_number": target.cinema_number,
                        "time_slot": target.time_slot.isoformat() if target.time_slot else None
                    }
                ))
                loop.close()

        except Exception as e:
            logger.error(f"Error in schedule_deleted event handler: {e}")

    logger.info("Database event handlers setup completed")