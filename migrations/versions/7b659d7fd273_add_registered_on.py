"""add registered_on

Revision ID: 7b659d7fd273
Revises: 899627fcbda3
Create Date: 2025-04-23 20:05:47.968689

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b659d7fd273'
down_revision = '899627fcbda3'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add registered_on as NULLABLE, with a server_default so existing rows get a value.
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column(
            'registered_on',
            sa.DateTime(),
            nullable=True,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ))

    # 2) Back-fill just in case (should be no-ops if #1 worked):
    op.execute(
        "UPDATE users SET registered_on = CURRENT_TIMESTAMP WHERE registered_on IS NULL"
    )

    # 3) Rebuild the table to make registered_on non-nullable and drop the default
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'registered_on',
            existing_type=sa.DateTime(),
            nullable=False,
            server_default=None
        )


def downgrade():
    with op.batch_alter_table('users', reflect=True) as batch_op:
        batch_op.drop_column('registered_on')
    # ### end Alembic commands ###
