"""Unit tests for todo API endpoints HTTP layer."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.api.v1.todos import (
    create_todo,
    list_todos,
    get_todo,
    update_todo,
    delete_todo,
    claim_todo,
    unclaim_todo,
    complete_todo,
    uncomplete_todo,
    add_shared_user,
    remove_shared_user,
    list_shared_users,
    update_todo_visibility,
)
from app.models.user import User
from app.schemas.todo import (
    Priority,
    TodoClaimCreate,
    TodoCreate,
    TodoRead,
    TodoShareCreate,
    TodoUpdate,
    TodoVisibilityUpdate,
    Visibility,
)


@pytest.fixture
def mock_db():
  """Create a mock database session."""
  return Mock()


@pytest.fixture
def mock_user():
  """Create a mock user."""
  user = Mock(spec=User)
  user.id = 1
  user.email = "test@example.com"
  return user


@pytest.fixture
def mock_household_member_or_404():
  """Mock get_household_member_or_404 dependency."""
  household = Mock()
  household.id = 1
  membership = Mock()
  return household, membership


class TestCreateTodoEndpoint:
  """Test create_todo endpoint."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_create_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo creation."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.create_todo.return_value = mock_todo

    todo_in = TodoCreate(
        title="Test Todo",
        priority=Priority.MEDIUM,
        visibility=Visibility.HOUSEHOLD,
    )

    result = create_todo(
        household_id=1,
        todo_in=todo_in,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo
    mock_service.create_todo.assert_called_once()

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_create_todo_value_error_returns_400(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test that ValueError is mapped to 400."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.create_todo.side_effect = ValueError("Invalid data")

    todo_in = TodoCreate(
        title="Test Todo",
        visibility=Visibility.SHARED,
        shared_user_ids=[],
    )

    with pytest.raises(HTTPException) as exc_info:
      create_todo(
          household_id=1,
          todo_in=todo_in,
          current_user=mock_user,
          db=mock_db,
      )

    assert exc_info.value.status_code == 400


class TestListTodosEndpoint:
  """Test list_todos endpoint."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_list_todos_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo listing."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todos = [Mock(spec=TodoRead), Mock(spec=TodoRead)]
    mock_service.get_visible_todos.return_value = mock_todos

    result = list_todos(
        household_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todos
    mock_service.get_visible_todos.assert_called_once()

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_list_todos_with_filters(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test listing todos with filters."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.get_visible_todos.return_value = []

    list_todos(
        household_id=1,
        current_user=mock_user,
        db=mock_db,
        priority="high",
        status="incomplete",
        sort="priority",
        order="desc",
    )

    call_args = mock_service.get_visible_todos.call_args
    assert call_args[1]["filters"]["priority"] == "high"
    assert call_args[1]["filters"]["status"] == "incomplete"
    assert call_args[1]["sort_field"] == "priority"
    assert call_args[1]["sort_order"] == "desc"


class TestGetTodoEndpoint:
  """Test get_todo endpoint."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_get_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo retrieval."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.get_todo.return_value = mock_todo

    result = get_todo(
        household_id=1,
        todo_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_get_todo_not_found_returns_404(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test that ValueError is mapped to 404."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.get_todo.side_effect = ValueError("Todo not found")

    with pytest.raises(HTTPException) as exc_info:
      get_todo(
          household_id=1,
          todo_id=999,
          current_user=mock_user,
          db=mock_db,
      )

    assert exc_info.value.status_code == 404

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_get_todo_permission_error_returns_403(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test that PermissionError is mapped to 403."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.get_todo.side_effect = PermissionError("No permission")

    with pytest.raises(HTTPException) as exc_info:
      get_todo(
          household_id=1,
          todo_id=1,
          current_user=mock_user,
          db=mock_db,
      )

    assert exc_info.value.status_code == 403


class TestUpdateTodoEndpoint:
  """Test update_todo endpoint."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_update_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo update."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.update_todo.return_value = mock_todo

    todo_update = TodoUpdate(title="Updated Title")

    result = update_todo(
        household_id=1,
        todo_id=1,
        todo_update=todo_update,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_update_todo_permission_error_returns_403(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test that PermissionError is mapped to 403."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.update_todo.side_effect = PermissionError("No permission")

    todo_update = TodoUpdate(title="Updated Title")

    with pytest.raises(HTTPException) as exc_info:
      update_todo(
          household_id=1,
          todo_id=1,
          todo_update=todo_update,
          current_user=mock_user,
          db=mock_db,
      )

    assert exc_info.value.status_code == 403


class TestDeleteTodoEndpoint:
  """Test delete_todo endpoint."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_delete_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo deletion."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.delete_todo.return_value = None

    result = delete_todo(
        household_id=1,
        todo_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result is None
    mock_service.delete_todo.assert_called_once()

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_delete_todo_not_found_returns_404(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test that ValueError is mapped to 404."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.delete_todo.side_effect = ValueError("Todo not found")

    with pytest.raises(HTTPException) as exc_info:
      delete_todo(
          household_id=1,
          todo_id=999,
          current_user=mock_user,
          db=mock_db,
      )

    assert exc_info.value.status_code == 404


class TestClaimEndpoints:
  """Test claim management endpoints."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_claim_todo_self_claim(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test self-claiming a todo."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.get_todo.return_value = mock_todo
    mock_service.claim_todo.return_value = Mock()

    result = claim_todo(
        household_id=1,
        todo_id=1,
        claim_in=None,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo
    # Should call claim_todo with claim_for_user_id=None
    call_args = mock_service.claim_todo.call_args
    assert call_args[1]["claim_for_user_id"] is None

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_claim_todo_for_others(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test claiming a todo for another user."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.get_todo.return_value = mock_todo
    mock_service.claim_todo.return_value = Mock()

    claim_in = TodoClaimCreate(user_id=2)

    result = claim_todo(
        household_id=1,
        todo_id=1,
        claim_in=claim_in,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo
    # Should call claim_todo with claim_for_user_id=2
    call_args = mock_service.claim_todo.call_args
    assert call_args[1]["claim_for_user_id"] == 2

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_unclaim_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo unclaim."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.unclaim_todo.return_value = None

    result = unclaim_todo(
        household_id=1,
        todo_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result is None
    mock_service.unclaim_todo.assert_called_once()


class TestCompletionEndpoints:
  """Test completion management endpoints."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_complete_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo completion."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.get_todo.return_value = mock_todo
    mock_service.complete_todo.return_value = Mock()

    result = complete_todo(
        household_id=1,
        todo_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_uncomplete_todo_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful todo uncompletion."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.uncomplete_todo.return_value = None

    result = uncomplete_todo(
        household_id=1,
        todo_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result is None
    mock_service.uncomplete_todo.assert_called_once()


class TestVisibilityEndpoints:
  """Test visibility management endpoints."""

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_update_todo_visibility_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful visibility update."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_todo = Mock(spec=TodoRead)
    mock_service.update_todo_visibility.return_value = mock_todo

    visibility_update = TodoVisibilityUpdate(
        visibility=Visibility.SHARED,
        shared_user_ids=[2,
                         3],
    )

    result = update_todo_visibility(
        household_id=1,
        todo_id=1,
        visibility_update=visibility_update,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_todo

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_add_shared_user_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful shared user addition."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_share = Mock()
    mock_service.add_shared_user.return_value = mock_share

    share_in = TodoShareCreate(user_id=2)

    result = add_shared_user(
        household_id=1,
        todo_id=1,
        share_in=share_in,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_share

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_remove_shared_user_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful shared user removal."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_service.remove_shared_user.return_value = None

    result = remove_shared_user(
        household_id=1,
        todo_id=1,
        user_id=2,
        current_user=mock_user,
        db=mock_db,
    )

    assert result is None

  @patch("app.api.v1.todos.get_household_member_or_404")
  @patch("app.api.v1.todos.TodoService")
  def test_list_shared_users_success(
      self,
      mock_service,
      mock_get_member,
      mock_db,
      mock_user):
    """Test successful shared users listing."""
    mock_get_member.return_value = (Mock(), Mock())
    mock_shares = [Mock(), Mock()]
    mock_service.list_shared_users.return_value = mock_shares

    result = list_shared_users(
        household_id=1,
        todo_id=1,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == mock_shares
