"""
security.py
------------
Shared input-validation and safe-error-handling helpers used by every tool
in server.py.

These implement the two "best practices" required by the assignment:
  1. Input Sanitization  -> the validate_* functions below
  2. Error Disclosure    -> the safe_tool_call() decorator + logger setup

Design note: every validate_* function either returns the cleaned value or
raises ValueError with a short, user-safe message. server.py never passes
raw, un-validated user input to the database or to smtplib.
"""

import functools
import logging
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging: full detail goes to a local log file only. Nothing written here
# is ever sent back to the MCP client -- that's what keeps stack traces,
# internal file paths, and SMTP error text from leaking to whoever is
# talking to the server (our "Error Disclosure" best practice).
# ---------------------------------------------------------------------------
LOG_PATH = Path(__file__).parent / "server.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mcp_productivity_server")


# ---------------------------------------------------------------------------
# Input validation ("Input Sanitization" best practice)
# ---------------------------------------------------------------------------

_ALLOWED_PRIORITIES = {"low", "medium", "high"}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_CRLF_RE = re.compile(r"[\r\n]")
MAX_TEXT_LEN = 500


def validate_title(title: str) -> str:
    """Task title: non-empty, reasonable length, no embedded newlines."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Title must be a non-empty string.")
    if len(title) > MAX_TEXT_LEN:
        raise ValueError(f"Title must be {MAX_TEXT_LEN} characters or fewer.")
    if _CRLF_RE.search(title):
        raise ValueError("Title cannot contain newline characters.")
    return title.strip()


def validate_due_date(due_date: str) -> str:
    """Due date must be a plain YYYY-MM-DD string (no time, no SQL, nothing else)."""
    if not isinstance(due_date, str) or not _DATE_RE.match(due_date):
        raise ValueError("due_date must be in YYYY-MM-DD format.")
    return due_date


def validate_priority(priority: str) -> str:
    """Priority must be one of a fixed allow-list -- never trusted freeform text."""
    if not isinstance(priority, str) or priority.lower() not in _ALLOWED_PRIORITIES:
        raise ValueError("priority must be one of: low, medium, high.")
    return priority.lower()


def validate_email_address(address: str) -> str:
    """Recipient address: basic shape check + reject header-injection characters."""
    if not isinstance(address, str) or not _EMAIL_RE.match(address):
        raise ValueError("recipient_email is not a valid email address.")
    if _CRLF_RE.search(address):
        raise ValueError("recipient_email cannot contain newline characters.")
    return address


def validate_email_header_text(value: str, field_name: str) -> str:
    """
    For values that become an EMAIL HEADER (currently: subject). Reject
    embedded CR/LF -- this is the actual header-injection vector, since a
    newline inside a header value could be used to smuggle in a fake extra
    header (like a hidden Bcc:).
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    if _CRLF_RE.search(value):
        raise ValueError(f"{field_name} cannot contain raw newline characters.")
    if len(value) > MAX_TEXT_LEN:
        raise ValueError(f"{field_name} is too long.")
    return value


def validate_email_body(value: str) -> str:
    """
    For the email BODY. Newlines are perfectly normal here (paragraph
    breaks) and are NOT a header-injection risk: the body is written via
    EmailMessage.set_content(), which always places it after the header
    section, so embedded newlines can't be used to forge additional
    headers the way they could in a header value. We only guard against
    unreasonably large input.
    """
    if not isinstance(value, str):
        raise ValueError("body must be a string.")
    if len(value) > MAX_TEXT_LEN * 4:
        raise ValueError("body is too long.")
    return value


# ---------------------------------------------------------------------------
# Safe error handling ("Error Disclosure" best practice)
# ---------------------------------------------------------------------------

def safe_tool_call(func):
    """
    Decorator for every @mcp.tool(). Any exception is logged in full detail
    server-side only, then replaced with a short, generic message before it
    reaches the MCP client. This prevents leaking database file paths, SMTP
    credentials/error text, or Python stack traces to whoever is talking to
    the server.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as exc:
            # Validation errors are already short, safe, user-facing
            # messages written by us -- fine to return directly.
            logger.info("Validation error in %s: %s", func.__name__, exc)
            return {"success": False, "error": str(exc)}
        except Exception:
            # Anything else (DB errors, SMTP errors, etc.) is unexpected.
            # Log the full detail locally; tell the client nothing specific.
            logger.exception("Unhandled error in %s", func.__name__)
            return {
                "success": False,
                "error": "An internal error occurred while processing your "
                "request. Please try again.",
            }

    return wrapper