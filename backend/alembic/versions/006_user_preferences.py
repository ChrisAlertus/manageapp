"""User preferences table

Revision ID: 006
Revises: 005
Create Date: 2025-12-21 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
  # Create user_preferences table
  # Note: DateTime(timezone=True) creates TIMESTAMP WITH TIME ZONE in PostgreSQL
  # and is handled correctly by SQLAlchemy for SQLite (which doesn't distinguish)
  op.create_table(
      'user_preferences',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('user_id',
                sa.Integer(),
                nullable=False),
      sa.Column(
          'preferred_currency',
          sa.String(length=3),
          nullable=False,
          server_default='CAD'),
      sa.Column(
          'timezone',
          sa.String(length=50),
          nullable=False,
          server_default='UTC'),
      sa.Column(
          'language',
          sa.String(length=10),
          nullable=False,
          server_default='en'),
      sa.Column('created_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.Column('updated_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.ForeignKeyConstraint(['user_id'],
                              ['users.id'],
                              ondelete='CASCADE'),
      sa.PrimaryKeyConstraint('id'))
  # Create indexes
  op.create_index(
      'ix_user_preferences_id',
      'user_preferences',
      ['id'],
      unique=False)
  op.create_index(
      'ix_user_preferences_user_id',
      'user_preferences',
      ['user_id'],
      unique=True)


def downgrade() -> None:
  # Drop indexes
  op.drop_index(
      op.f('ix_user_preferences_user_id'),
      table_name='user_preferences')
  op.drop_index(op.f('ix_user_preferences_id'), table_name='user_preferences')
  # Drop table
  op.drop_table('user_preferences')
