"""Add invitations table

Revision ID: 003
Revises: 002
Create Date: 2025-12-21 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
  op.create_table(
      'invitations',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('token_hash',
                sa.String(length=64),
                nullable=False),
      sa.Column('email',
                sa.String(),
                nullable=False),
      sa.Column('household_id',
                sa.Integer(),
                nullable=False),
      sa.Column('inviter_user_id',
                sa.Integer(),
                nullable=True),
      sa.Column('accepted_by_user_id',
                sa.Integer(),
                nullable=True),
      sa.Column('role',
                sa.String(),
                nullable=False),
      sa.Column('status',
                sa.String(),
                nullable=False),
      sa.Column('expires_at',
                sa.DateTime(),
                nullable=False),
      sa.Column('last_sent_at',
                sa.DateTime(),
                nullable=True),
      sa.Column('resend_count',
                sa.Integer(),
                nullable=False),
      sa.Column('created_at',
                sa.DateTime(),
                nullable=False),
      sa.Column('updated_at',
                sa.DateTime(),
                nullable=False),
      sa.Column('accepted_at',
                sa.DateTime(),
                nullable=True),
      sa.Column('cancelled_at',
                sa.DateTime(),
                nullable=True),
      sa.ForeignKeyConstraint(['household_id'],
                              ['households.id'],
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['inviter_user_id'],
                              ['users.id'],
                              ondelete='SET NULL'),
      sa.ForeignKeyConstraint(['accepted_by_user_id'],
                              ['users.id'],
                              ondelete='SET NULL'),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('token_hash',
                          name='uq_invitations_token_hash'))
  op.create_index('ix_invitations_id', 'invitations', ['id'], unique=False)
  op.create_index(
      'ix_invitations_token_hash',
      'invitations',
      ['token_hash'],
      unique=True)
  op.create_index(
      'ix_invitations_email',
      'invitations',
      ['email'],
      unique=False)
  op.create_index(
      'ix_invitations_household_id',
      'invitations',
      ['household_id'],
      unique=False)
  op.create_index(
      'ix_invitations_status',
      'invitations',
      ['status'],
      unique=False)
  op.create_index(
      'ix_invitations_expires_at',
      'invitations',
      ['expires_at'],
      unique=False)
  op.create_index(
      'ix_invitations_inviter_user_id',
      'invitations',
      ['inviter_user_id'],
      unique=False)
  op.create_index(
      'ix_invitations_accepted_by_user_id',
      'invitations',
      ['accepted_by_user_id'],
      unique=False)
  op.create_index(
      'ix_invitations_household_status',
      'invitations',
      ['household_id',
       'status'],
      unique=False)
  op.create_index(
      'ix_invitations_household_email',
      'invitations',
      ['household_id',
       'email'],
      unique=False)


def downgrade() -> None:
  op.drop_index('ix_invitations_household_email', table_name='invitations')
  op.drop_index('ix_invitations_household_status', table_name='invitations')
  op.drop_index('ix_invitations_accepted_by_user_id', table_name='invitations')
  op.drop_index('ix_invitations_inviter_user_id', table_name='invitations')
  op.drop_index('ix_invitations_expires_at', table_name='invitations')
  op.drop_index('ix_invitations_status', table_name='invitations')
  op.drop_index('ix_invitations_household_id', table_name='invitations')
  op.drop_index('ix_invitations_email', table_name='invitations')
  op.drop_index('ix_invitations_token_hash', table_name='invitations')
  op.drop_index('ix_invitations_id', table_name='invitations')
  op.drop_table('invitations')
