"""Added in the tee-id

Revision ID: 9b3749f733d6
Revises: 42a194cfe674
Create Date: 2024-12-26 14:31:38.840188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b3749f733d6'
down_revision = '42a194cfe674'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rounds', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tee_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_rounds_tee_id', 'tees', ['tee_id'], ['teeID'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rounds', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('tee_id')

    # ### end Alembic commands ###
