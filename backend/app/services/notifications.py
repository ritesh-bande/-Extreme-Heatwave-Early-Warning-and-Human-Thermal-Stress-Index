"""
Notification clients for dispatching alerts.

Provides a NotificationClient interface with a DryRun fallback when
Twilio credentials are not available.
"""

import logging
from abc import ABC, abstractmethod
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationClient(ABC):
    @abstractmethod
    def send_sms(self, to_number: str, message: str) -> None:
        pass

    @abstractmethod
    def send_whatsapp(self, to_number: str, message: str) -> None:
        pass


class DryRunClient(NotificationClient):
    """
    Dummy client that just logs messages instead of sending them.
    Used when Twilio credentials are not configured.
    """
    def send_sms(self, to_number: str, message: str) -> None:
        logger.info(f"\n[DRY RUN SMS to {to_number}]\n{message}\n")

    def send_whatsapp(self, to_number: str, message: str) -> None:
        logger.info(f"\n[DRY RUN WhatsApp to {to_number}]\n{message}\n")


class TwilioClientWrapper(NotificationClient):
    """
    Actual Twilio API client.
    """
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
            self.from_number = from_number
        except ImportError:
            logger.error("twilio library not installed. Falling back to DryRun.")
            self.client = None

    def send_sms(self, to_number: str, message: str) -> None:
        if not self.client:
            return
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"Twilio SMS sent. SID: {message_obj.sid}")
        except Exception as e:
            logger.error(f"Failed to send Twilio SMS: {e}")

    def send_whatsapp(self, to_number: str, message: str) -> None:
        if not self.client:
            return
            
        try:
            # Twilio WhatsApp numbers require the whatsapp: prefix
            from_wa = f"whatsapp:{self.from_number}"
            to_wa = f"whatsapp:{to_number}"
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_wa,
                to=to_wa
            )
            logger.info(f"Twilio WhatsApp sent. SID: {message_obj.sid}")
        except Exception as e:
            logger.error(f"Failed to send Twilio WhatsApp: {e}")


def get_notification_client() -> NotificationClient:
    """Factory to get the appropriate notification client based on config."""
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        logger.info("Initializing real Twilio client.")
        return TwilioClientWrapper(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_FROM_NUMBER
        )
    
    return DryRunClient()
