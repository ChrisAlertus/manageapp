"""Invitation endpoints (send, list, accept, resend, cancel)."""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


def ensure_timezone_aware(dt: datetime) -> datetime:
  """Ensure datetime is timezone-aware (UTC).

  Args:
    dt: Datetime that may be naive or aware.

  Returns:
    Timezone-aware datetime in UTC.
  """
  if dt.tzinfo is None:
    return dt.replace(tzinfo=timezone.utc)
  return dt


from app.api.deps import (
    get_current_active_user,
    get_db,
    get_household_owner_or_403,
)
from app.core.config import settings
from app.models.household_member import HouseholdMember
from app.models.invitation import Invitation
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
from app.services.invitation_utils import (
    build_invitation_accept_url,
    generate_invitation_token,
    hash_invitation_token,
    normalize_email,
)


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

  now = datetime.now(timezone.utc)
  invitee_email = normalize_email(str(invitation_in.email))

  # Prevent inviting an existing household member
  existing_member = (
      db.query(HouseholdMember).join(
          User,
          HouseholdMember.user_id == User.id).filter(
              HouseholdMember.household_id == household_id,
              User.email == invitee_email,
          ).first())
  if existing_member is not None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User is already a member of this household",
    )

  # Duplicate prevention: only one active pending invitation per email+household
  # Note: SQLAlchemy handles timezone conversion at DB level for
  # DateTime(timezone=True)
  existing_pending = (
      db.query(Invitation).filter(
          Invitation.household_id == household_id,
          Invitation.email == invitee_email,
          Invitation.status == "pending",
          Invitation.expires_at > now,
      ).first())
  if existing_pending is not None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="An active invitation is already pending for this email",
    )

  expires_hours = (
      invitation_in.expires_in_hours if invitation_in.expires_in_hours
      is not None else settings.INVITATION_EXPIRE_HOURS)
  expires_at = now + timedelta(hours=expires_hours)

  token = generate_invitation_token()
  token_hash = hash_invitation_token(token)

  invitation = Invitation(
      token_hash=token_hash,
      email=invitee_email,
      household_id=household_id,
      inviter_user_id=current_user.id,
      role=invitation_in.role,
      status="pending",
      expires_at=expires_at,
      last_sent_at=None,
      resend_count=0,
  )
  db.add(invitation)
  # Do not commit yet; only flush to get the invitation ID/obj for sending the email.
  db.flush()
  db.refresh(invitation)

  accept_url = build_invitation_accept_url(token)
  try:
    message_client.send_invitation(
        to_email=invitee_email,
        inviter_email=current_user.email,
        household_name=household.name,
        accept_url=accept_url,
    )
  except EmailSendError:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to send invitation email",
    )

  invitation.last_sent_at = now
  db.commit()
  db.refresh(invitation)
  return invitation


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
  _household, _ = get_household_owner_or_403(household_id, current_user, db)
  now = datetime.now(timezone.utc)
  invitations = (
      db.query(Invitation).filter(
          Invitation.household_id == household_id,
          Invitation.status == "pending",
          Invitation.expires_at > now,
      ).order_by(Invitation.created_at.desc()).all())
  return invitations


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
  invitation = (
      db.query(Invitation).filter(
          Invitation.id == invitation_id,
          Invitation.household_id == household_id,
      ).first())
  if invitation is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Invitation not found",
    )
  if invitation.status != "pending":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Only pending invitations can be resent",
    )

  now = datetime.now(timezone.utc)

  # If expired, refresh token + expiration to create a new active invite.
  token = None
  expires_at = ensure_timezone_aware(invitation.expires_at)
  if expires_at <= now:
    token = generate_invitation_token()
    invitation.token_hash = hash_invitation_token(token)
    invitation.expires_at = now + timedelta(
        hours=settings.INVITATION_EXPIRE_HOURS)
  else:
    token = generate_invitation_token()
    invitation.token_hash = hash_invitation_token(token)

  accept_url = build_invitation_accept_url(token)
  try:
    message_client.send_invitation(
        to_email=invitation.email,
        inviter_email=current_user.email,
        household_name=household.name,
        accept_url=accept_url,
    )
  except EmailSendError:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to send invitation email",
    )

  invitation.resend_count += 1
  invitation.last_sent_at = now
  db.commit()
  db.refresh(invitation)
  return invitation


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
  _household, _ = get_household_owner_or_403(household_id, current_user, db)
  invitation = (
      db.query(Invitation).filter(
          Invitation.id == invitation_id,
          Invitation.household_id == household_id,
      ).first())
  if invitation is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Invitation not found",
    )
  if invitation.status != "pending":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Only pending invitations can be cancelled",
    )

  now = datetime.now(timezone.utc)
  invitation.status = "cancelled"
  invitation.cancelled_at = now
  db.commit()
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
  now = datetime.now(timezone.utc)
  token_hash = hash_invitation_token(accept_in.token.strip())
  invitation = (
      db.query(Invitation).filter(Invitation.token_hash == token_hash).first())
  if invitation is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Invitation not found",
    )
  if invitation.status != "pending":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invitation is not pending",
    )
  # Ensure expires_at is timezone-aware for comparison
  expires_at = ensure_timezone_aware(invitation.expires_at)
  if expires_at <= now:
    invitation.status = "expired"
    db.commit()
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invitation has expired",
    )

  if normalize_email(current_user.email) != invitation.email:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This invitation is for a different email address",
    )

  existing_membership = (
      db.query(HouseholdMember).filter(
          HouseholdMember.household_id == invitation.household_id,
          HouseholdMember.user_id == current_user.id,
      ).first())
  if existing_membership is not None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User is already a member of this household",
    )

  membership = HouseholdMember(
      household_id=invitation.household_id,
      user_id=current_user.id,
      role=invitation.role,
  )
  db.add(membership)

  invitation.status = "accepted"
  invitation.accepted_at = now
  invitation.accepted_by_user_id = current_user.id

  db.commit()
  return InvitationAcceptResponse(
      household_id=invitation.household_id,
      role=invitation.role,
  )
