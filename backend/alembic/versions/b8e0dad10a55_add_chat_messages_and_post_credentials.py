"""add_chat_messages_and_post_credentials

Revision ID: b8e0dad10a55
Revises: d1b6f6d30a86
Create Date: 2026-08-16 00:48:33.697615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e0dad10a55'
down_revision: Union[str, Sequence[str], None] = 'd1b6f6d30a86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'chat_messages' not in tables:
        op.create_table(
            'chat_messages',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('conversation_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_chat_messages_conversation_id'), 'chat_messages', ['conversation_id'], unique=False)
        op.create_index(op.f('ix_chat_messages_sender_id'), 'chat_messages', ['sender_id'], unique=False)

    post_cols = [c['name'] for c in insp.get_columns('community_posts')]
    with op.batch_alter_table('community_posts') as batch_op:
        if 'credential_id' not in post_cols:
            batch_op.add_column(sa.Column('credential_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(None, 'user_credentials', ['credential_id'], ['id'], ondelete='SET NULL')

    mission_cols = [c['name'] for c in insp.get_columns('missions')]
    with op.batch_alter_table('missions') as batch_op:
        if 'created_at' not in mission_cols:
            batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.alter_column('goal_id', existing_type=sa.INTEGER(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('missions') as batch_op:
        batch_op.alter_column('goal_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column('created_at')

    with op.batch_alter_table('community_posts') as batch_op:
        batch_op.drop_column('credential_id')

    op.drop_index(op.f('ix_chat_messages_sender_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_conversation_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
