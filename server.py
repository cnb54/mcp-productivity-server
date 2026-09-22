"""
server.py
---------
MCP server entry point for the Personal Productivity domain (CS/applied-AI
class project).

Exposes:
  - Tool:   add_task                  (SQLite-backed task tracker)
  - Tool:   send_task_reminder_email  (Gmail SMTP, real authentication)
  - Prompt: daily_planner_prompt

Built with the official MCP Python SDK's FastMCP interface. The
@mcp.tool() / @mcp.prompt() decorator pattern below follows the quickstart
example in the MCP Python SDK README:
https://github.com/modelcontextprotocol/python-sdk
"""

from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

import db
import email_utils
from security import (
    logger,
    safe_tool_call,
    validate_due_date,
    validate_email_address,
    validate_email_text,
    validate_priority,
    validate_title,
)

# Load secrets from .env (see .env.example) into environment variables
# before anything else runs.
load_dotenv(Path(__file__).parent / ".env")

# Make sure the SQLite tasks table exists before we accept any tool calls.
db.init_db()

mcp = FastMCP("personal-productivity-server")


@mcp.tool()
@safe_tool_call
def add_task(title: str, due_date: str, priority: str = "medium") -> dict:
    """
    Add a task to the task list.

    Args:
        title: Short description of the task.
        due_date: Due date in YYYY-MM-DD format.
        priority: One of "low", "medium", "high".
    """
    clean_title = validate_title(title)
    clean_due_date = validate_due_date(due_date)
    clean_priority = validate_priority(priority)

    task_id = db.insert_task(clean_title, clean_due_date, clean_priority)
    logger.info("Task %s added: %s", task_id, clean_title)

    return {
        "success": True,
        "task_id": task_id,
        "title": clean_title,
        "due_date": clean_due_date,
        "priority": clean_priority,
    }


@mcp.tool()
@safe_tool_call
def send_task_reminder_email(recipient_email: str, subject: str, body: str) -> dict:
    """
    Send a task reminder email via Gmail SMTP.

    Args:
        recipient_email: Recipient's email address.
        subject: Email subject line.
        body: Email body text.
    """
    clean_recipient = validate_email_address(recipient_email)
    clean_subject = validate_email_text(subject, "subject")
    clean_body = validate_email_text(body, "body")

    email_utils.send_email(clean_recipient, clean_subject, clean_body)
    logger.info("Reminder email sent to %s", clean_recipient)

    return {
        "success": True,
        "recipient_email": clean_recipient,
        "subject": clean_subject,
    }


@mcp.prompt()
def daily_planner_prompt() -> str:
    """
    Reusable prompt template: pulls the current task list out of the
    database and asks the model to turn it into a prioritized daily plan.
    """
    tasks = db.list_all_tasks()

    if not tasks:
        task_lines = "(no tasks yet -- use add_task to add some)"
    else:
        task_lines = "\n".join(
            f"- [{t['priority']}] {t['title']} "
            f"(due {t['due_date']}, status: {t['status']})"
            for t in tasks
        )

    return (
        "You are my personal productivity assistant. Here is my current "
        "task list:\n\n"
        f"{task_lines}\n\n"
        "Please turn this into a prioritized plan for today: order the "
        "tasks by urgency and priority, flag anything overdue, and suggest "
        "a realistic order to tackle them in."
    )


if __name__ == "__main__":
    mcp.run()
