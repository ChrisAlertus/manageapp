"""Invitation business logic service."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.household_member import HouseholdMember
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.invitation import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreate,
)
from app.services.email import MessageClient, MessageSendError
from app.services.invitation_utils import (
    build_invitation_accept_url,
    generate_invitation_token,
    hash_invitation_token,
    normalize_email,
)


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


class InvitationService:
  """Service for invitation business logic."""

  @staticmethod
  def send_invitation(
      db: Session,
      household_id: int,
      invitation_in: InvitationCreate,
      inviter_user_id: int,
      inviter_email: str,
      household_name: str,
      message_client: MessageClient,
  ) -> Invitation:
    """Send a household invitation email.

    Behavior:
      - Prevents duplicate pending invitations for the same email+household.
      - Stores only a hash of the invitation token (raw token is emailed).

    Args:
      db: Database session.
      household_id: The household ID.
      invitation_in: Invitation creation data.
      inviter_user_id: ID of the user sending the invitation.
      inviter_email: Email of the user sending the invitation.
      household_name: Name of the household.
      message_client: Message client for sending emails.

    Returns:
      Created invitation object.

    Raises:
      ValueError: If user is already a member or duplicate invitation exists.
      MessageSendError: If email sending fails.
    """
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
      raise ValueError("User is already a member of this household")

    # Duplicate prevention: only one active pending invitation per email+household
    existing_pending = (
        db.query(Invitation).filter(
            Invitation.household_id == household_id,
            Invitation.email == invitee_email,
            Invitation.status == "pending",
            Invitation.expires_at > now,
        ).first())
    if existing_pending is not None:
      raise ValueError("An active invitation is already pending for this email")

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
        inviter_user_id=inviter_user_id,
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
          inviter_email=inviter_email,
          household_name=household_name,
          accept_url=accept_url,
      )
    except MessageSendError as e:
      db.rollback()
      raise MessageSendError(
          f"Failed to send invitation email: {str(e)}") from e

    invitation.last_sent_at = now
    db.commit()
    db.refresh(invitation)
    return invitation

  @staticmethod
  def list_pending_invitations(
      db: Session,
      household_id: int,
  ) -> List[Invitation]:
    """List pending (non-expired) invitations for a household.

    Args:
      db: Database session.
      household_id: The household ID.

    Returns:
      List of pending invitations.
    """
    now = datetime.now(timezone.utc)
    invitations = (
        db.query(Invitation).filter(
            Invitation.household_id == household_id,
            Invitation.status == "pending",
            Invitation.expires_at > now,
        ).order_by(Invitation.created_at.desc()).all())
    return invitations

  @staticmethod
  def resend_invitation(
      db: Session,
      household_id: int,
      invitation_id: int,
      inviter_email: str,
      household_name: str,
      message_client: MessageClient,
  ) -> Invitation:
    """Resend an invitation.

    Args:
      db: Database session.
      household_id: The household ID.
      invitation_id: The invitation ID.
      inviter_email: Email of the user resending the invitation.
      household_name: Name of the household.
      message_client: Message client for sending emails.

    Returns:
      Updated invitation object.

    Raises:
      ValueError: If invitation not found or not pending.
      MessageSendError: If email sending fails.
    """
    invitation = (
        db.query(Invitation).filter(
            Invitation.id == invitation_id,
            Invitation.household_id == household_id,
        ).first())
    if invitation is None:
      raise ValueError("Invitation not found")
    if invitation.status != "pending":
      raise ValueError("Only pending invitations can be resent")

    now = datetime.now(timezone.utc)

    # If expired, refresh token + expiration to create a new active invite.
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
          inviter_email=inviter_email,
          household_name=household_name,
          accept_url=accept_url,
      )
    except MessageSendError as e:
      raise MessageSendError(
          f"Failed to send invitation email: {str(e)}") from e

    invitation.resend_count += 1
    invitation.last_sent_at = now
    db.commit()
    db.refresh(invitation)
    return invitation

  @staticmethod
  def cancel_invitation(
      db: Session,
      household_id: int,
      invitation_id: int,
  ) -> None:
    """Cancel an invitation.

    Args:
      db: Database session.
      household_id: The household ID.
      invitation_id: The invitation ID.

    Raises:
      ValueError: If invitation not found or not pending.
    """
    invitation = (
        db.query(Invitation).filter(
            Invitation.id == invitation_id,
            Invitation.household_id == household_id,
        ).first())
    if invitation is None:
      raise ValueError("Invitation not found")
    if invitation.status != "pending":
      raise ValueError("Only pending invitations can be cancelled")

    now = datetime.now(timezone.utc)
    invitation.status = "cancelled"
    invitation.cancelled_at = now
    db.commit()

  @staticmethod
  def accept_invitation(
      db: Session,
      accept_in: InvitationAcceptRequest,
      user_id: int,
      user_email: str,
  ) -> InvitationAcceptResponse:
    """Accept an invitation by token.

    Args:
      db: Database session.
      accept_in: Invitation accept request with token.
      user_id: ID of the user accepting the invitation.
      user_email: Email of the user accepting the invitation.

    Returns:
      Invitation accept response with household_id and role.

    Raises:
      ValueError: If invitation not found, not pending, expired, wrong email, or already a member.
    """
    now = datetime.now(timezone.utc)
    token_hash = hash_invitation_token(accept_in.token.strip())
    invitation = (
        db.query(Invitation).filter(
            Invitation.token_hash == token_hash).first())
    if invitation is None:
      raise ValueError("Invitation not found")
    if invitation.status != "pending":
      raise ValueError("Invitation is not pending")
    # Ensure expires_at is timezone-aware for comparison
    expires_at = ensure_timezone_aware(invitation.expires_at)
    if expires_at <= now:
      invitation.status = "expired"
      db.commit()
      raise ValueError("Invitation has expired")

    if normalize_email(user_email) != invitation.email:
      raise ValueError("This invitation is for a different email address")

    existing_membership = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == invitation.household_id,
            HouseholdMember.user_id == user_id,
        ).first())
    if existing_membership is not None:
      raise ValueError("User is already a member of this household")

    membership = HouseholdMember(
        household_id=invitation.household_id,
        user_id=user_id,
        role=invitation.role,
    )
    db.add(membership)

    invitation.status = "accepted"
    invitation.accepted_at = now
    invitation.accepted_by_user_id = user_id

    db.commit()
    return InvitationAcceptResponse(
        household_id=invitation.household_id,
        role=invitation.role,
    )
