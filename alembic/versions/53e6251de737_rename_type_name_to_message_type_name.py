"""Rename type_name to message_type_name

Revision ID: 53e6251de737
Revises: 391fc0462f5a
Create Date: 2024-09-10 13:53:26.664205

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '53e6251de737'
down_revision: Union[str, None] = '391fc0462f5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing unique constraint
    op.drop_constraint('uq_from_type_message', 'messages', type_='unique')

    # Rename the column from 'type_name' to 'message_type_name'
    op.alter_column('messages', 'type_name', new_column_name='message_type_name')

    # Recreate the unique constraint with the new column name
    op.create_unique_constraint('uq_from_type_message', 'messages', ['from_alias', 'message_type_name', 'message_persisted_ms'])

def downgrade() -> None:
    # Drop the new unique constraint
    op.drop_constraint('uq_from_type_message', 'messages', type_='unique')

    # Rename the column back from 'message_type_name' to 'type_name'
    op.alter_column('messages', 'message_type_name', new_column_name='type_name')

    # Recreate the original unique constraint
    op.create_unique_constraint('uq_from_type_message', 'messages', ['from_alias', 'type_name', 'message_persisted_ms'])
