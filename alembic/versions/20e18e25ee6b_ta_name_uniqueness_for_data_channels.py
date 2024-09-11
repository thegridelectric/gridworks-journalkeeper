"""ta/name uniqueness for data channels

Revision ID: 20e18e25ee6b
Revises: fc0ccbb3b83e
Create Date: 2024-09-11 11:47:19.359194

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20e18e25ee6b'
down_revision: Union[str, None] = 'fc0ccbb3b83e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_name_terminal_asset', 'data_channels', ['terminal_asset_alias', 'name'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_name_terminal_asset', 'data_channels', type_='unique')
    # ### end Alembic commands ###