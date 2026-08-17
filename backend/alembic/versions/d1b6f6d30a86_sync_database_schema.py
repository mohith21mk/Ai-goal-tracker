"""sync database schema

Revision ID: d1b6f6d30a86
Revises: cfd5123488f3
Create Date: 2026-08-15 20:00:24.318754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b6f6d30a86'
down_revision: Union[str, Sequence[str], None] = 'cfd5123488f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'user_credentials' not in tables:
        op.create_table(
            'user_credentials',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('credential_type', sa.String(length=50), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('tier', sa.String(length=50), nullable=True),
            sa.Column('xp_value', sa.Integer(), nullable=True),
            sa.Column('evidence_type', sa.String(length=50), nullable=False),
            sa.Column('evidence_id', sa.String(length=255), nullable=True),
            sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'slug', name='uq_user_credential_slug')
        )
        op.create_index(op.f('ix_user_credentials_user_id'), 'user_credentials', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_credentials_user_id'), table_name='user_credentials')
    op.drop_table('user_credentials')
