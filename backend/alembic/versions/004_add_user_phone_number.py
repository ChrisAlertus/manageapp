"""Add phone_number to users table

Revision ID: 004
Revises: 003
Create Date: 2025-12-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
  # Add phone_number column to users table
  op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
  # Create index for phone_number (useful for future SMS/WhatsApp lookups)
  op.create_index(
      'ix_users_phone_number',
      'users',
      ['phone_number'],
      unique=False)


def downgrade() -> None:
  op.drop_index('ix_users_phone_number', table_name='users')
  op.drop_column('users', 'phone_number')
