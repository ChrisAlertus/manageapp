"""Message service abstraction (email, SMS, WhatsApp).

Design goals:
  - Testable: injectable dependency, easy to mock
  - Simple: console provider by default
  - Fast: sending is a single HTTP call
  - Future-proof: supports multi-channel (email, SMS, WhatsApp)
"""

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class MessageSendError(RuntimeError):
  """Raised when a message provider fails to send."""


# Backward compatibility alias
EmailSendError = MessageSendError


class MessageClient(Protocol):
  """Interface for sending messages (email, SMS, WhatsApp).

  Future-proof abstraction that supports multiple channels.
  For now, only email is implemented. SMS/WhatsApp can be added later.
  """

  def send_invitation(
      self,
      *,
      to_email: str | None = None,
      to_phone: str | None = None,
      inviter_email: str,
      household_name: str,
      accept_url: str,
  ) -> None:
    """Send an invitation via email and/or SMS/WhatsApp.

    Args:
      to_email: Recipient email address (optional if to_phone provided)
      to_phone: Recipient phone number (optional if to_email provided)
      inviter_email: Email of the user sending the invitation
      household_name: Name of the household
      accept_url: URL to accept the invitation

    Raises:
      MessageSendError: If sending fails
    """


# Backward compatibility alias
EmailClient = MessageClient


@dataclass(frozen=True)
class ConsoleMessageClient:
  """No-op message client that logs outgoing messages."""

  from_email: str = settings.EMAIL_FROM

  def send_invitation(
      self,
      *,
      to_email: str | None = None,
      to_phone: str | None = None,
      inviter_email: str,
      household_name: str,
      accept_url: str,
  ) -> None:
    """Log invitation message (console mode)."""
    channels = []
    if to_email:
      channels.append(f"email:{to_email}")
    if to_phone:
      channels.append(f"phone:{to_phone}")

    logger.info(
        "Invitation message (console): channels=[%s] from=%s inviter=%s household=%s url=%s",
        ", ".join(channels) if channels else "none",
        self.from_email,
        inviter_email,
        household_name,
        accept_url,
    )


# Backward compatibility alias
ConsoleEmailClient = ConsoleMessageClient


@dataclass(frozen=True)
class ResendMessageClient:
  """Resend email client using Resend API.

  Modern, developer-friendly email API with excellent DX.
  Free tier: 3,000 emails/month.
  """

  api_key: str
  from_email: str = settings.EMAIL_FROM

  def send_invitation(
      self,
      *,
      to_email: str | None = None,
      to_phone: str | None = None,
      inviter_email: str,
      household_name: str,
      accept_url: str,
  ) -> None:
    """Send invitation via email (SMS/WhatsApp not yet implemented)."""
    if not to_email:
      raise MessageSendError(
          "Email address required. SMS/WhatsApp not yet implemented.")

    subject = f"You've been invited to join {household_name}"
    text = (
        f"{inviter_email} invited you to join '{household_name}'.\n\n"
        f"Accept your invitation:\n{accept_url}\n")

    payload = {
        "from": self.from_email,
        "to": to_email,
        "subject": subject,
        "text": text,
    }

    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
    }

    try:
      with httpx.Client(timeout=5.0) as client:
        resp = client.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
        )
      if resp.status_code >= 300:
        raise MessageSendError(
            f"Resend error {resp.status_code}: {resp.text[:200]}")
    except MessageSendError:
      raise
    except Exception as e:
      raise MessageSendError(str(e)) from e


# Backward compatibility alias
ResendEmailClient = ResendMessageClient


def get_message_client() -> MessageClient:
  """FastAPI dependency for resolving the message client.

  Returns:
    MessageClient implementation based on EMAIL_PROVIDER setting.

  Raises:
    MessageSendError: If provider is configured but API key is missing.
  """
  provider = (settings.EMAIL_PROVIDER or "console").strip().lower()

  if provider == "resend":
    if not settings.RESEND_API_KEY:
      raise MessageSendError("RESEND_API_KEY is not configured")
    return ResendMessageClient(api_key=settings.RESEND_API_KEY)

  return ConsoleMessageClient()


# Backward compatibility alias
def get_email_client() -> MessageClient:
  """Backward compatibility alias for get_message_client()."""
  return get_message_client()
