"""Add households and household_members tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
  # Create households table
  op.create_table(
      'households',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('name',
                sa.String(),
                nullable=False),
      sa.Column('description',
                sa.Text(),
                nullable=True),
      sa.Column('created_by',
                sa.Integer(),
                nullable=True),
      sa.Column('created_at',
                sa.DateTime(),
                nullable=False),
      sa.Column('updated_at',
                sa.DateTime(),
                nullable=False),
      sa.ForeignKeyConstraint(['created_by'],
                              ['users.id'],
                              ondelete='SET NULL'),
      sa.PrimaryKeyConstraint('id'))
  op.create_index('ix_households_id', 'households', ['id'], unique=False)
  op.create_index('ix_households_name', 'households', ['name'], unique=False)
  op.create_index(
      'ix_households_created_by',
      'households',
      ['created_by'],
      unique=False)

  # Create household_members table
  op.create_table(
      'household_members',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('household_id',
                sa.Integer(),
                nullable=False),
      sa.Column('user_id',
                sa.Integer(),
                nullable=False),
      sa.Column('role',
                sa.String(),
                nullable=False),
      sa.Column('joined_at',
                sa.DateTime(),
                nullable=False),
      sa.ForeignKeyConstraint(['household_id'],
                              ['households.id'],
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['user_id'],
                              ['users.id'],
                              ondelete='CASCADE'),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint(
          'household_id',
          'user_id',
          name='uq_household_member'))
  op.create_index(
      'ix_household_members_id',
      'household_members',
      ['id'],
      unique=False)
  op.create_index(
      'ix_household_members_household_id',
      'household_members',
      ['household_id'],
      unique=False)
  op.create_index(
      'ix_household_members_user_id',
      'household_members',
      ['user_id'],
      unique=False)
  op.create_index(
      'ix_household_members_household_role',
      'household_members',
      ['household_id',
       'role'],
      unique=False)


def downgrade() -> None:
  op.drop_index(
      'ix_household_members_household_role',
      table_name='household_members')
  op.drop_index('ix_household_members_user_id', table_name='household_members')
  op.drop_index(
      'ix_household_members_household_id',
      table_name='household_members')
  op.drop_index('ix_household_members_id', table_name='household_members')
  op.drop_table('household_members')
  op.drop_index('ix_households_name', table_name='households')
  op.drop_index('ix_households_id', table_name='households')
  op.drop_table('households')
