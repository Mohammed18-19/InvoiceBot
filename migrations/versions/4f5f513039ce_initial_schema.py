"""initial schema

Revision ID: 4f5f513039ce
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '4f5f513039ce'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='free'),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('default_payment_link', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table('invoices',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('client_name', sa.String(255), nullable=False),
        sa.Column('client_email', sa.String(255), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('payment_link', sa.String(500), nullable=True),
        sa.Column('tone', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('stage1_delay', sa.Integer(), nullable=True),
        sa.Column('stage2_delay', sa.Integer(), nullable=True),
        sa.Column('stage3_delay', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('marked_paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('email_schedules',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('invoice_id', sa.String(36), nullable=False),
        sa.Column('stage', sa.Integer(), nullable=False),
        sa.Column('send_at', sa.DateTime(), nullable=False),
        sa.Column('sent', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('email_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('invoice_id', sa.String(36), nullable=False),
        sa.Column('stage', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('sendgrid_message_id', sa.String(200), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('email_drafts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('invoice_id', sa.String(36), nullable=True),
        sa.Column('email_type', sa.String(50), nullable=True),
        sa.Column('to_address', sa.String(255), nullable=False),
        sa.Column('from_email', sa.String(255), nullable=True),
        sa.Column('from_name', sa.String(255), nullable=True),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('email_drafts')
    op.drop_table('email_logs')
    op.drop_table('email_schedules')
    op.drop_table('invoices')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
