"""data channel has terminal asset alias

Revision ID: 8307576a573f
Revises: ed9df502fb56
Create Date: 2024-08-08 20:47:19.142669

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8307576a573f"
down_revision: Union[str, None] = "ed9df502fb56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "data_channels", sa.Column("in_power_metering", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "data_channels",
        sa.Column(
            "terminal_asset_alias",
            sa.String(),
            nullable=False,
            server_default="hw1.isone.me.versant.keene.beech.ta",
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("data_channels", "terminal_asset_alias")
    op.drop_column("data_channels", "in_power_metering")
    # ### end Alembic commands ###
