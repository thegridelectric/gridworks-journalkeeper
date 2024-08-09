"""Add foreign key constraint and update relationships

Revision ID: b829ccf129c3
Revises: f183a8a6ac28
Create Date: 2024-07-20 12:34:54.493598

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b829ccf129c3"
down_revision: Union[str, None] = "f183a8a6ac28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a named foreign key constraint
    op.create_foreign_key(
        "fk_readings_data_channel_id",  # Constraint name
        "readings",
        "data_channels",
        ["data_channel_id"],
        ["id"],
    )


def downgrade() -> None:
    # Drop the named foreign key constraint
    op.drop_constraint(
        "fk_readings_data_channel_id",
        "readings",
        type_="foreignkey",  # Constraint name
    )
