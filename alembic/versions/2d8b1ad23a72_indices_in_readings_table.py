"""indices in readings table

Revision ID: 2d8b1ad23a72
Revises: b08628433b03
Create Date: 2024-10-13 08:41:17.962929

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d8b1ad23a72"
down_revision: Union[str, None] = "b08628433b03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        "ix_data_channel_time", "readings", ["data_channel_id", "time_ms"], unique=False
    )
    op.create_index("ix_message_id", "readings", ["message_id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_message_id", table_name="readings")
    op.drop_index("ix_data_channel_time", table_name="readings")
    # ### end Alembic commands ###
