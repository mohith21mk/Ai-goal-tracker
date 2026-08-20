"""add_data_to_notifications

Revision ID: e9f7dad20a66
Revises: b8e0dad10a55
Create Date: 2026-08-16 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f7dad20a66'
down_revision: Union[str, Sequence[str], None] = 'b8e0dad10a55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    if 'notifications' in tables:
        notif_cols = [c['name'] for c in insp.get_columns('notifications')]
        with op.batch_alter_table('notifications') as batch_op:
            if 'data' not in notif_cols:
                batch_op.add_column(sa.Column('data', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('notifications') as batch_op:
        batch_op.drop_column('data')
