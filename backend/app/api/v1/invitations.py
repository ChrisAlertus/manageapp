"""Invitation endpoints (send, list, accept, resend, cancel)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_household_owner_or_403,
)
from app.models.household import Household
from app.models.user import User
from app.schemas.invitation import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationRead,
)
from app.services.email import (
    EmailClient,  # Backward compatibility alias
    EmailSendError,  # Backward compatibility alias
    MessageClient,
    MessageSendError,
    get_email_client,  # Backward compatibility alias
    get_message_client,
)
from app.services.invitation_service import InvitationService


router = APIRouter()


@router.post(
    "/households/{household_id}/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def send_invitation(
    household_id: int,
    invitation_in: InvitationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    message_client: MessageClient = Depends(get_message_client),
):
  """
  Send a household invitation email (owners only).

  Behavior:
    - Prevents duplicate pending invitations for the same email+household.
    - Stores only a hash of the invitation token (raw token is emailed).
  """
  household, _ = get_household_owner_or_403(household_id, current_user, db)

  try:
    return InvitationService.send_invitation(
        db=db,
        household_id=household_id,
        invitation_in=invitation_in,
        inviter_user_id=current_user.id,
        inviter_email=current_user.email,
        household_name=household.name,
        message_client=message_client,
    )
  except ValueError as e:
    error_detail = str(e)
    if "already pending" in error_detail.lower():
      raise HTTPException(
          status_code=status.HTTP_409_CONFLICT,
          detail=error_detail,
      )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_detail,
    )
  except MessageSendError as e:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(e),
    )


@router.get(
    "/households/{household_id}/invitations",
    response_model=List[InvitationRead],
)
def list_pending_invitations(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """List pending (non-expired) invitations for a household (owners only)."""
  get_household_owner_or_403(household_id, current_user, db)
  return InvitationService.list_pending_invitations(
      db=db,
      household_id=household_id,
  )


@router.post(
    "/households/{household_id}/invitations/{invitation_id}/resend",
    response_model=InvitationRead,
)
def resend_invitation(
    household_id: int,
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    message_client: MessageClient = Depends(get_message_client),
):
  """Resend an invitation (owners only)."""
  household, _ = get_household_owner_or_403(household_id, current_user, db)

  try:
    return InvitationService.resend_invitation(
        db=db,
        household_id=household_id,
        invitation_id=invitation_id,
        inviter_email=current_user.email,
        household_name=household.name,
        message_client=message_client,
    )
  except ValueError as e:
    error_detail = str(e)
    if "not found" in error_detail.lower():
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=error_detail,
      )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_detail,
    )
  except MessageSendError as e:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(e),
    )


@router.post(
    "/households/{household_id}/invitations/{invitation_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_invitation(
    household_id: int,
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """Cancel an invitation (owners only)."""
  get_household_owner_or_403(household_id, current_user, db)

  try:
    InvitationService.cancel_invitation(
        db=db,
        household_id=household_id,
        invitation_id=invitation_id,
    )
  except ValueError as e:
    error_detail = str(e)
    if "not found" in error_detail.lower():
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=error_detail,
      )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_detail,
    )

  return None


@router.post(
    "/invitations/accept",
    response_model=InvitationAcceptResponse,
)
def accept_invitation(
    accept_in: InvitationAcceptRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """Accept an invitation by token (authenticated)."""
  try:
    return InvitationService.accept_invitation(
        db=db,
        accept_in=accept_in,
        user_id=current_user.id,
        user_email=current_user.email,
    )
  except ValueError as e:
    error_detail = str(e)
    if "not found" in error_detail.lower():
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=error_detail,
      )
    if "different email" in error_detail.lower():
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail=error_detail,
      )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_detail,
    )
