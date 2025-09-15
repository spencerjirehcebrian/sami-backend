"""add_schedule_performance_indexes

Revision ID: 59cf6a80bc33
Revises: 67b4e523cd2c
Create Date: 2025-09-16 05:40:06.878759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59cf6a80bc33'
down_revision: Union[str, Sequence[str], None] = '67b4e523cd2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add performance indexes for schedule queries

    # 1. Composite index for cinema-specific queries with time filtering
    op.create_index(
        'idx_schedules_cinema_time',
        'schedules',
        ['cinema_id', 'time_slot']
    )

    # 2. Composite index for time-based queries with status filtering
    op.create_index(
        'idx_schedules_time_status',
        'schedules',
        ['time_slot', 'status']
    )

    # 3. Composite index for movie-specific queries with time filtering
    op.create_index(
        'idx_schedules_movie_time',
        'schedules',
        ['movie_id', 'time_slot']
    )

    # 4. Single index for general time-based queries and sorting
    op.create_index(
        'idx_schedules_time_only',
        'schedules',
        ['time_slot']
    )

    # 5. Partial index for active schedules (most common case)
    op.create_index(
        'idx_schedules_status',
        'schedules',
        ['status'],
        postgresql_where=sa.text("status = 'active'")
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove performance indexes for schedule queries
    op.drop_index('idx_schedules_status', 'schedules')
    op.drop_index('idx_schedules_time_only', 'schedules')
    op.drop_index('idx_schedules_movie_time', 'schedules')
    op.drop_index('idx_schedules_time_status', 'schedules')
    op.drop_index('idx_schedules_cinema_time', 'schedules')
