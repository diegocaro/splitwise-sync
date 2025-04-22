"""IMAP email client for fetching messages from Gmail."""

import logging
from dataclasses import dataclass
from typing import List, Optional

from imap_tools.mailbox import MailBox
from imap_tools.message import MailMessage
from imap_tools.query import AND

from ..config import GMAIL_APP_PASSWORD, GMAIL_USERNAME
from .models import EmailMessage

logger = logging.getLogger(__name__)


@dataclass
class EmailCredentials:
    """Model for email credentials."""

    username: str
    password: str


class ImapEmailClient:
    """Client for fetching messages from Gmail using IMAP protocol."""

    def __init__(self, credentials: Optional[EmailCredentials] = None) -> None:
        """Initialize the IMAP Gmail client.

        Args:
            credentials: Optional email credentials. If not provided,
                         credentials will be loaded from environment variables.
        """
        self.credentials = credentials or self._load_credentials_from_env()
        self.imap_server = "imap.gmail.com"

    def _load_credentials_from_env(self) -> EmailCredentials:
        """Load email credentials from environment variables."""

        username = GMAIL_USERNAME
        password = GMAIL_APP_PASSWORD

        if not username or not password:
            raise ValueError(
                "Gmail credentials not found in environment variables. "
                "Please set GMAIL_USERNAME and GMAIL_APP_PASSWORD."
            )

        return EmailCredentials(username=username, password=password)

    def _connect(self) -> MailBox:
        """Connect to the IMAP server and login.

        Returns:
            An authenticated MailBox connection
        """
        mailbox = MailBox(self.imap_server)
        mailbox.login(self.credentials.username, self.credentials.password, "INBOX")
        return mailbox

    def _convert_message(self, msg: MailMessage) -> EmailMessage:
        """Convert imap_tools MailMessage to our EmailMessage format.

        Args:
            msg: The MailMessage from imap_tools
            msg_id: The message ID

        Returns:
            Converted EmailMessage
        """
        # Get the plain text body or HTML if plain text not available
        body = msg.text or msg.html

        return EmailMessage(
            uid=str(msg.uid),
            subject=msg.subject,
            sender=msg.from_,
            to=msg.to,
            date=msg.date,
            body=body,
        )

    def fetch_unread_from_sender(
        self, sender_email: str, mark_as_read: bool = True
    ) -> List[EmailMessage]:
        """Search for unread emails from a specific sender.

        Args:
            sender_email: The email address of the sender to filter by
            mark_as_read: Whether to mark emails as read after fetching (default: True)

        Returns:
            A list of unread email messages from the specified sender
        """
        messages: List[EmailMessage] = []

        with self._connect() as mailbox:
            criteria = AND(seen=False, from_=sender_email)

            # Set mark_seen=False to keep emails unread
            for msg in mailbox.fetch(criteria, mark_seen=mark_as_read):
                email_msg = self._convert_message(msg)
                messages.append(email_msg)

        logger.info(f"Found {len(messages)} unread messages from {sender_email}")

        return messages

    def mark_unread(self, email_id: str) -> None:
        """Mark an email as unread.

        Args:
            email_id: The ID of the email to mark as unread
        """
        with self._connect() as mailbox:
            mailbox.flag(email_id, "\\Seen", False)
            logger.info(f"Marked email {email_id} as unread")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Example usage: Search for unread emails from Banco Edwards
    client = ImapEmailClient()
    emails = client.fetch_unread_from_sender("enviodigital@bancoedwards.cl")
    for email in emails:
        logger.info(f"Subject: {email.subject}")
        logger.info(f"From: {email.sender}")
        logger.info(f"Date: {email.date}")
        logger.info(f"ID: {email.uid}")
        # logger.info(f"Body: {email.body}")
