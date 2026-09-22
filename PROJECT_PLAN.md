# Project Plan — Personal Productivity MCP Server

This file is our working scratchpad for the class project so you (Christina) can
see the whole design in one place and refer back to it later, e.g. when
writing your reflection or prepping for the quiz on this code. It is **not**
a required deliverable — feel free to delete it before submitting, or keep it,
it doesn't hurt.

## Domain
Personal Productivity: a task tracker with an email-reminder tool.

## Components (Part 1)

**Tool 1 — `add_task(title, due_date, priority)`**
- Adds a task to a local SQLite database (`tasks.db`).
- Uses parameterized SQL queries (never string-concatenated SQL) — this is
  our Input Sanitization best practice, and SQL injection is the exploit
  we'll demo against it.
- Validates `due_date` is a real `YYYY-MM-DD` date and `priority` is one of
  `low` / `medium` / `high` before touching the database at all.

**Tool 2 — `send_task_reminder_email(recipient_email, subject, body)`**
- Sends a real email via Gmail SMTP, authenticated with a Gmail "App
  Password" loaded from `.env` (this is our authentication + secret
  management piece).
- Validates the recipient looks like a real email address and rejects any
  input containing raw CR/LF characters — this blocks email header
  injection (e.g. an attacker sneaking a hidden `Bcc:` line into the
  subject/body to silently CC themselves on every reminder). This is the
  second angle of our Input Sanitization best practice.

**Prompt — `daily_planner_prompt`**
- A reusable MCP prompt template that takes the current task list and asks
  the model to produce a prioritized daily plan. This is what "prompts" in
  MCP are for: a reusable, parameterized instruction template the *client*
  (Claude Desktop) can offer the user, as opposed to a tool the model calls
  itself.

## Best practices (Part 2A) — Input Sanitization + Error Disclosure

1. **Input Sanitization**
   - SQL injection prevention in `add_task` (parameterized queries +
     allow-listed `priority` values + regex-validated `due_date`).
   - Email header injection prevention in `send_task_reminder_email`
     (reject embedded `\r`/`\n`, validate email format with a regex).
   - Exploit demos live in `exploits/exploit_sql_injection.py` and
     `exploits/exploit_header_injection.py`.

2. **Error Disclosure**
   - Every tool wraps its logic in try/except. Internal exceptions
     (stack traces, file paths, SMTP error text that could contain
     account details) are logged to a local file (`server.log`, gitignored)
     but never returned to the MCP client — the client only ever sees a
     short, generic error message.
   - Exploit demo in `exploits/exploit_error_disclosure.py` triggers a real
     internal error and shows the sanitized client-facing response next to
     the (locally-logged-only) raw exception.

## Best practices (Part 2B)
- Claude Desktop config file included: `claude_desktop_config.example.json`.

## File layout
```
mcp-productivity-server/
├── server.py                       # MCP server entry point: tools + prompt
├── db.py                           # SQLite helpers (parameterized queries)
├── email_utils.py                  # SMTP sending + header-injection defense
├── security.py                     # shared validation + safe-error helpers
├── exploits/
│   ├── exploit_sql_injection.py
│   ├── exploit_header_injection.py
│   └── exploit_error_disclosure.py
├── .env.example                    # committed (placeholders only)
├── .env                            # NOT committed (real secrets)
├── .gitignore
├── requirements.txt
├── README.md
└── claude_desktop_config.example.json
```

## Not going in the GitHub repo
Per the assignment instructions, these go to Canvas only:
- The (GitHub link / domain / best practices) table
- The architecture diagram
- The reflection paragraphs
