"""Make invitation datetime columns timezone-aware

Revision ID: 005
Revises: 004
Create Date: 2025-12-21 19:43:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
  # For PostgreSQL, convert DateTime to TIMESTAMP WITH TIME ZONE
  # For SQLite, this is a no-op (SQLite doesn't distinguish timezone-aware/naive)
  # Existing data will be preserved, and new data will be timezone-aware

  # Note: SQLite doesn't support timezone-aware datetimes natively,
  # but SQLAlchemy handles the conversion. For PostgreSQL, we need to
  # alter the column type.

  # Check if we're using PostgreSQL
  bind = op.get_bind()
  if bind.dialect.name == 'postgresql':
    # Convert all datetime columns to timezone-aware
    op.alter_column(
        'invitations',
        'expires_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'')
    op.alter_column(
        'invitations',
        'last_sent_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        nullable=True,
        postgresql_using='last_sent_at AT TIME ZONE \'UTC\'')
    op.alter_column(
        'invitations',
        'created_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        postgresql_using='created_at AT TIME ZONE \'UTC\'')
    op.alter_column(
        'invitations',
        'updated_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        postgresql_using='updated_at AT TIME ZONE \'UTC\'')
    op.alter_column(
        'invitations',
        'accepted_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        nullable=True,
        postgresql_using='accepted_at AT TIME ZONE \'UTC\'')
    op.alter_column(
        'invitations',
        'cancelled_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        nullable=True,
        postgresql_using='cancelled_at AT TIME ZONE \'UTC\'')
  # For SQLite, no changes needed - SQLAlchemy handles it at the ORM level


def downgrade() -> None:
  # Revert to naive datetimes (not recommended, but provided for completeness)
  bind = op.get_bind()
  if bind.dialect.name == 'postgresql':
    op.alter_column(
        'invitations',
        'expires_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True))
    op.alter_column(
        'invitations',
        'last_sent_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        nullable=True)
    op.alter_column(
        'invitations',
        'created_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True))
    op.alter_column(
        'invitations',
        'updated_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True))
    op.alter_column(
        'invitations',
        'accepted_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        nullable=True)
    op.alter_column(
        'invitations',
        'cancelled_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        nullable=True)
