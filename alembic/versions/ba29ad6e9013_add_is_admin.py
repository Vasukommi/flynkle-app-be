"""add is_admin column"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'ba29ad6e9013'
down_revision: Union[str, Sequence[str], None] = '8fc6b18b1fb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
