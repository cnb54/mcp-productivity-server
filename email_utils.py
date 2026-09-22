"""
email_utils.py
--------------
Sends task reminder emails via Gmail SMTP, authenticated with credentials
loaded from environment variables (populated from .env by server.py at
startup -- see .env.example).

Reference: the smtplib/EmailMessage usage pattern is adapted from the
official Python docs example:
https://docs.python.org/3/library/smtplib.html#smtp-example
"""

import os
import smtplib
from email.message import EmailMessage


def send_email(recipient_email: str, subject: str, body: str) -> None:
    """
    Send a plain-text email via Gmail SMTP (SSL, port 465).

    Credentials come from environment variables -- never hardcoded, never
    logged, never returned to the caller. Raises on failure; the caller
    (server.py, via the safe_tool_call decorator) is responsible for
    turning any exception into a safe, generic response.
    """
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = EmailMessage()
    msg["From"] = gmail_address
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    # timeout=10 keeps a network hiccup (or an unreachable SMTP server) from
    # hanging the whole MCP tool call indefinitely.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(msg)
