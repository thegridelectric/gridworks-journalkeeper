"""unique triple per ta for data channels

Revision ID: b08628433b03
Revises: 20e18e25ee6b
Create Date: 2024-09-11 12:40:14.002367

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b08628433b03"
down_revision: Union[str, None] = "20e18e25ee6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "unique_triple_per_ta",
        "data_channels",
        [
            "terminal_asset_alias",
            "about_node_name",
            "captured_by_node_name",
            "telemetry_name",
        ],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_triple_per_ta", "data_channels", type_="unique")
    # ### end Alembic commands ###
