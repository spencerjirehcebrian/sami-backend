"""add_forecast_system_tables

Revision ID: 0edb4b07b264
Revises: d40d2afa67f3
Create Date: 2025-09-24 11:45:47.381564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0edb4b07b264'
down_revision: Union[str, Sequence[str], None] = 'd40d2afa67f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create forecasts table
    op.create_table('forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date_range_start', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('date_range_end', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='generating'),
        sa.Column('optimization_parameters', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('total_schedules_generated', sa.Integer(), nullable=False, server_default='0')
    )

    # Create prediction_data table
    op.create_table('prediction_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('forecast_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('error_margin', sa.Float(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['forecast_id'], ['forecasts.id'], ondelete='CASCADE')
    )

    # Add forecast_id column to schedules table
    op.add_column('schedules', sa.Column('forecast_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint for forecast_id
    op.create_foreign_key('fk_schedules_forecast_id', 'schedules', 'forecasts', ['forecast_id'], ['id'], ondelete='CASCADE')

    # Create index on forecast_id for better query performance
    op.create_index('idx_schedules_forecast', 'schedules', ['forecast_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index('idx_schedules_forecast', 'schedules')

    # Drop foreign key constraint
    op.drop_constraint('fk_schedules_forecast_id', 'schedules', type_='foreignkey')

    # Drop forecast_id column from schedules
    op.drop_column('schedules', 'forecast_id')

    # Drop prediction_data table (will also drop its foreign key constraint)
    op.drop_table('prediction_data')

    # Drop forecasts table
    op.drop_table('forecasts')
