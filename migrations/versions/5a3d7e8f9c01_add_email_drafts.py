"""Add email drafts table

Revision ID: 5a3d7e8f9c01
Revises: 502bb0fe4904
Create Date: 2026-05-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a3d7e8f9c01'
down_revision = '502bb0fe4904'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'email_drafts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('invoice_id', sa.String(length=36), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('email_type', sa.String(length=50), nullable=True),
        sa.Column('to_address', sa.String(length=255), nullable=False),
        sa.Column('from_email', sa.String(length=255), nullable=True),
        sa.Column('from_name', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('email_drafts')
