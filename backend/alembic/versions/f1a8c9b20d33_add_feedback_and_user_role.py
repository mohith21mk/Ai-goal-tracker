"""add_feedback_and_user_role

Revision ID: f1a8c9b20d33
Revises: e9f7dad20a66
Create Date: 2026-08-16 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a8c9b20d33'
down_revision: Union[str, Sequence[str], None] = 'e9f7dad20a66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. Add role column to users if not present
    user_cols = [c['name'] for c in insp.get_columns('users')]
    with op.batch_alter_table('users') as batch_op:
        if 'role' not in user_cols:
            batch_op.add_column(sa.Column('role', sa.String(length=50), nullable=False, server_default='user'))

    # 2. Create feedback table if not present
    existing_tables = insp.get_table_names()
    if 'feedback' not in existing_tables:
        op.create_table(
            'feedback',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False, server_default='Normal'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
            sa.Column('admin_notes', sa.Text(), nullable=True),
            sa.Column('page_url', sa.Text(), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('resolved_at', sa.DateTime(), nullable=True)
        )
        op.create_index('idx_feedback_user', 'feedback', ['user_id'])
        op.create_index('idx_feedback_status', 'feedback', ['status'])
        op.create_index('idx_feedback_category', 'feedback', ['category'])
        op.create_index('idx_feedback_created', 'feedback', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'feedback' in existing_tables:
        op.drop_index('idx_feedback_created', table_name='feedback')
        op.drop_index('idx_feedback_category', table_name='feedback')
        op.drop_index('idx_feedback_status', table_name='feedback')
        op.drop_index('idx_feedback_user', table_name='feedback')
        op.drop_table('feedback')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('role')
