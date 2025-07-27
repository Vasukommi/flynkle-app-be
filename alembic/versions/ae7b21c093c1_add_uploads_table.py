"""add uploads table"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'ae7b21c093c1'
down_revision: Union[str, Sequence[str], None] = 'ba29ad6e9013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'uploads',
        sa.Column('upload_id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('bucket', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('uploads')
