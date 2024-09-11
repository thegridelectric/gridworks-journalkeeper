"""non-null field constraints for nodal hourly energy

Revision ID: fc0ccbb3b83e
Revises: 53e6251de737
Create Date: 2024-09-11 11:46:29.340249

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fc0ccbb3b83e'
down_revision: Union[str, None] = '53e6251de737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('nodal_hourly_energy', 'hour_start_s',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('nodal_hourly_energy', 'watt_hours',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('nodal_hourly_energy', 'watt_hours',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('nodal_hourly_energy', 'hour_start_s',
               existing_type=sa.BIGINT(),
               nullable=True)
    # ### end Alembic commands ###