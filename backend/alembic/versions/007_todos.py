"""Add todos, todo_claims, todo_completions, and todo_shares tables

This migration creates the complete todo system including:
- todos table with visibility support
- todo_claims table for assignment (users can claim todos for themselves or others)
- todo_completions table for tracking completion
- todo_shares table for shared visibility

Revision ID: 007
Revises: 006
Create Date: 2025-12-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
  # Create todos table
  op.create_table(
      'todos',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('title',
                sa.String(),
                nullable=False),
      sa.Column('description',
                sa.Text(),
                nullable=True),
      sa.Column('household_id',
                sa.Integer(),
                nullable=False),
      sa.Column('created_by',
                sa.Integer(),
                nullable=True),
      sa.Column(
          'priority',
          sa.String(),
          nullable=False,
          server_default='medium'),
      sa.Column('due_date',
                sa.DateTime(timezone=True),
                nullable=True),
      sa.Column('category',
                sa.String(),
                nullable=True),
      sa.Column(
          'visibility',
          sa.String(),
          nullable=False,
          server_default='household'),
      sa.Column('created_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.Column('updated_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.ForeignKeyConstraint(['household_id'],
                              ['households.id'],
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['created_by'],
                              ['users.id'],
                              ondelete='SET NULL'),
      sa.PrimaryKeyConstraint('id'))
  op.create_index('ix_todos_id', 'todos', ['id'], unique=False)
  op.create_index(
      'ix_todos_household_id',
      'todos',
      ['household_id'],
      unique=False)
  op.create_index('ix_todos_created_by', 'todos', ['created_by'], unique=False)
  op.create_index('ix_todos_priority', 'todos', ['priority'], unique=False)
  op.create_index('ix_todos_due_date', 'todos', ['due_date'], unique=False)
  op.create_index('ix_todos_category', 'todos', ['category'], unique=False)
  op.create_index('ix_todos_visibility', 'todos', ['visibility'], unique=False)
  op.create_index(
      'ix_todos_household_priority',
      'todos',
      ['household_id',
       'priority'],
      unique=False)

  # Create todo_claims table
  op.create_table(
      'todo_claims',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('todo_id',
                sa.Integer(),
                nullable=False),
      sa.Column('claimed_by',
                sa.Integer(),
                nullable=True),
      sa.Column('claimed_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.ForeignKeyConstraint(['todo_id'],
                              ['todos.id'],
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['claimed_by'],
                              ['users.id'],
                              ondelete='SET NULL'),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('todo_id',
                          name='uq_todo_claim_todo_id'))
  op.create_index('ix_todo_claims_id', 'todo_claims', ['id'], unique=False)
  op.create_index(
      'ix_todo_claims_todo_id',
      'todo_claims',
      ['todo_id'],
      unique=True)
  op.create_index(
      'ix_todo_claims_claimed_by',
      'todo_claims',
      ['claimed_by'],
      unique=False)

  # Create todo_completions table
  op.create_table(
      'todo_completions',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('todo_id',
                sa.Integer(),
                nullable=False),
      sa.Column('completed_by',
                sa.Integer(),
                nullable=True),
      sa.Column('completed_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.ForeignKeyConstraint(['todo_id'],
                              ['todos.id'],
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['completed_by'],
                              ['users.id'],
                              ondelete='SET NULL'),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('todo_id',
                          name='uq_todo_completion_todo_id'))
  op.create_index(
      'ix_todo_completions_id',
      'todo_completions',
      ['id'],
      unique=False)
  op.create_index(
      'ix_todo_completions_todo_id',
      'todo_completions',
      ['todo_id'],
      unique=True)
  op.create_index(
      'ix_todo_completions_completed_by',
      'todo_completions',
      ['completed_by'],
      unique=False)

  # Create todo_shares table
  op.create_table(
      'todo_shares',
      sa.Column('id',
                sa.Integer(),
                nullable=False),
      sa.Column('todo_id',
                sa.Integer(),
                nullable=False),
      sa.Column('user_id',
                sa.Integer(),
                nullable=False),
      sa.Column('created_at',
                sa.DateTime(timezone=True),
                nullable=False),
      sa.ForeignKeyConstraint(['todo_id'],
                              ['todos.id'],
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['user_id'],
                              ['users.id'],
                              ondelete='CASCADE'),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('todo_id',
                          'user_id',
                          name='uq_todo_share'))
  op.create_index('ix_todo_shares_id', 'todo_shares', ['id'], unique=False)
  op.create_index(
      'ix_todo_shares_todo_id',
      'todo_shares',
      ['todo_id'],
      unique=False)
  op.create_index(
      'ix_todo_shares_user_id',
      'todo_shares',
      ['user_id'],
      unique=False)
  op.create_index(
      'ix_todo_shares_todo_user',
      'todo_shares',
      ['todo_id',
       'user_id'],
      unique=False)


def downgrade() -> None:
  # Drop indexes for todo_shares
  op.drop_index('ix_todo_shares_todo_user', table_name='todo_shares')
  op.drop_index('ix_todo_shares_user_id', table_name='todo_shares')
  op.drop_index('ix_todo_shares_todo_id', table_name='todo_shares')
  op.drop_index('ix_todo_shares_id', table_name='todo_shares')
  op.drop_table('todo_shares')

  # Drop indexes for todo_completions
  op.drop_index(
      'ix_todo_completions_completed_by',
      table_name='todo_completions')
  op.drop_index('ix_todo_completions_todo_id', table_name='todo_completions')
  op.drop_index('ix_todo_completions_id', table_name='todo_completions')
  op.drop_table('todo_completions')

  # Drop indexes for todo_claims
  op.drop_index('ix_todo_claims_claimed_by', table_name='todo_claims')
  op.drop_index('ix_todo_claims_todo_id', table_name='todo_claims')
  op.drop_index('ix_todo_claims_id', table_name='todo_claims')
  op.drop_table('todo_claims')

  # Drop indexes for todos
  op.drop_index('ix_todos_household_priority', table_name='todos')
  op.drop_index('ix_todos_visibility', table_name='todos')
  op.drop_index('ix_todos_category', table_name='todos')
  op.drop_index('ix_todos_due_date', table_name='todos')
  op.drop_index('ix_todos_priority', table_name='todos')
  op.drop_index('ix_todos_created_by', table_name='todos')
  op.drop_index('ix_todos_household_id', table_name='todos')
  op.drop_index('ix_todos_id', table_name='todos')
  op.drop_table('todos')
