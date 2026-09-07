"""add_mission_logs_table

Revision ID: a1c9e8f7b204
Revises: f1a8c9b20d33
Create Date: 2026-09-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c9e8f7b204'
down_revision: Union[str, Sequence[str], None] = 'f1a8c9b20d33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'mission_logs' not in existing_tables:
        op.create_table(
            'mission_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('mission_id', sa.Integer(), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('completed_date', sa.String(length=50), nullable=False),
            sa.Column('completed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('xp_reward', sa.Integer(), server_default='10'),
            sa.UniqueConstraint('user_id', 'mission_id', 'completed_date', name='uq_mission_user_date')
        )
        op.create_index('idx_mission_logs_user_date', 'mission_logs', ['user_id', 'completed_date'])
        op.create_index('idx_mission_logs_mission_date', 'mission_logs', ['mission_id', 'completed_date'])

        # Backfill mission_logs from existing completed missions
        dialect_name = bind.dialect.name
        if dialect_name == 'postgresql':
            op.execute("""
                INSERT INTO mission_logs (user_id, mission_id, completed_date, completed_at, xp_reward)
                SELECT user_id, id, SUBSTRING(completed_at::text, 1, 10), completed_at, COALESCE(xp_reward, 10)
                FROM missions
                WHERE completed = 1 AND completed_at IS NOT NULL AND user_id IS NOT NULL
                ON CONFLICT (user_id, mission_id, completed_date) DO NOTHING
            """)
        else:
            op.execute("""
                INSERT OR IGNORE INTO mission_logs (user_id, mission_id, completed_date, completed_at, xp_reward)
                SELECT user_id, id, substr(completed_at, 1, 10), completed_at, COALESCE(xp_reward, 10)
                FROM missions
                WHERE completed = 1 AND completed_at IS NOT NULL AND user_id IS NOT NULL
            """)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'mission_logs' in existing_tables:
        op.drop_index('idx_mission_logs_mission_date', table_name='mission_logs')
        op.drop_index('idx_mission_logs_user_date', table_name='mission_logs')
        op.drop_table('mission_logs')
