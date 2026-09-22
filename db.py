"""
db.py
-----
SQLite-backed storage for tasks, used by the add_task tool and by the
daily_planner_prompt.

Reference: the parameterized-query pattern (using "?" placeholders) follows
the official Python docs example for sqlite3:
https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
"""

import os
import sqlite3
from pathlib import Path


def _db_path() -> Path:
    # Read the env var lazily (not at import time) so tests/exploits can
    # override TASKS_DB_PATH before the first real database call.
    #
    # A RELATIVE path (the default, "tasks.db") is resolved against this
    # file's own folder, not against the current working directory. This
    # matters because an MCP client (like Claude Desktop) launches this
    # server as a subprocess from its own working directory, not from
    # inside this project folder -- without this, sqlite3 would try to
    # create "tasks.db" in some unrelated folder and fail with
    # "unable to open database file".
    raw_path = Path(os.getenv("TASKS_DB_PATH", "tasks.db"))
    if raw_path.is_absolute():
        return raw_path
    return Path(__file__).parent / raw_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the tasks table if it doesn't exist yet. Safe to call on every startup."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def insert_task(title: str, due_date: str, priority: str) -> int:
    """
    Insert a task using a PARAMETERIZED query (the "?" placeholders below).

    This is what actually prevents SQL injection: title/due_date/priority
    are always passed to sqlite3 as separate data values, never
    string-concatenated into the SQL text, so the database engine can never
    interpret them as SQL syntax -- no matter what characters they contain.
    See exploits/exploit_sql_injection.py for a side-by-side demo against
    the vulnerable (string-concatenated) alternative.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, due_date, priority) VALUES (?, ?, ?)",
            (title, due_date, priority),
        )
        return cursor.lastrowid


def list_all_tasks() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, due_date, priority, status FROM tasks ORDER BY due_date ASC"
        ).fetchall()
        return [dict(row) for row in rows]
