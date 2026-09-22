# Personal Productivity MCP Server

A local [Model Context Protocol](https://modelcontextprotocol.io/) server built for an
applied AI class assignment. It gives an MCP client (Claude Desktop) two tools and one
prompt for managing a personal task list.

## What it does

| Type | Name | Description |
|---|---|---|
| Tool | `add_task` | Adds a task (title, due date, priority) to a local SQLite database. |
| Tool | `send_task_reminder_email` | Sends a real email via Gmail SMTP to remind someone about a task. |
| Prompt | `daily_planner_prompt` | Pulls your current task list and asks the model to turn it into a prioritized plan for the day. |

## Architecture

```
Claude Desktop (MCP client)
        │  stdio (subprocess)
        ▼
   server.py  (FastMCP app: registers tools + prompt)
        │
   ┌────┴─────┐
   ▼          ▼
 db.py    email_utils.py
   │          │
   ▼          ▼
tasks.db   Gmail SMTP (smtp.gmail.com:465)

security.py is used by every tool call: validates input before it reaches
db.py / email_utils.py, and wraps every tool in a try/except that logs full
error detail to server.log while returning only a generic message to the client.
```

A cleaner diagram version of this is submitted separately to Canvas.

## Setup

### 1. Clone and enter the project
```bash
git clone <your-repo-url>
cd mcp-productivity-server
```

### 2. Create the virtual environment
This project uses [uv](https://docs.astral.sh/uv/). If you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then create and activate the environment:
```bash
uv venv --python 3.12
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows
```

> **Apple Silicon Mac + Anaconda users:** if your terminal auto-activates Anaconda's
> `(base)` environment, run `conda deactivate` first. Otherwise `uv venv` may pick up
> an Intel-only Python running under Rosetta, which causes some dependencies
> (`cryptography`) to fail to build from source. Passing `--python 3.12` above tells
> uv to use its own native Python instead of whatever's on your `PATH`.

### 3. Install dependencies
```bash
uv pip install "mcp[cli]" python-dotenv
uv pip freeze > requirements.txt
```
(`mcp[cli]` includes the MCP Inspector dev tool used in step 5.)

### 4. Configure secrets
```bash
cp .env.example .env
```
Then edit `.env` and fill in:
- `GMAIL_ADDRESS` — the Gmail account the server will send reminder emails from.
- `GMAIL_APP_PASSWORD` — a Gmail **App Password** (not your normal password).
  Create one at <https://myaccount.google.com/apppasswords> (requires
  2-Step Verification to be turned on first).

`.env` is listed in `.gitignore` and is never committed.

### 5. Test the server on its own (optional but recommended)
```bash
mcp dev server.py
```
This opens the MCP Inspector in your browser, where you can call `add_task` and
`send_task_reminder_email` directly and see the `daily_planner_prompt` output,
without needing Claude Desktop yet.

### 6. Connect it to Claude Desktop
Open (or create) Claude Desktop's config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add the contents of [`claude_desktop_config.example.json`](./claude_desktop_config.example.json)
to the `"mcpServers"` object (merge it in if the file already has other servers
configured), then restart Claude Desktop. The paths in that file already point at
this project's venv and `server.py` — update them if you move the project folder.

## Running the security exploit demos

Each of the two best practices below has a script that attacks it and shows the
attack being blocked. Run these from the project root, with the venv activated:

```bash
python exploits/exploit_sql_injection.py
python exploits/exploit_header_injection.py
python exploits/exploit_error_disclosure.py
```

## Best practices implemented

**1. Input Sanitization** (`security.py`)
- `add_task`: due dates are regex-validated as `YYYY-MM-DD`, priority is checked
  against a fixed allow-list (`low`/`medium`/`high`), and all SQL is written with
  parameterized queries (`db.py`) so user input can never be interpreted as SQL —
  demonstrated in `exploits/exploit_sql_injection.py`.
- `send_task_reminder_email`: the recipient address is checked against an email
  regex, and the recipient/subject/body are all rejected if they contain raw
  `\r`/`\n` characters, which blocks email header injection (an attacker sneaking
  a hidden `Bcc:` line into the message) — demonstrated in
  `exploits/exploit_header_injection.py`.

**2. Error Disclosure** (`security.py`, `safe_tool_call` decorator)
- Every tool is wrapped so that unexpected exceptions (a database error, an SMTP
  authentication failure, etc.) are logged in full detail to `server.log`
  (gitignored, local-only) but the MCP client only ever receives a short,
  generic error message. Demonstrated in `exploits/exploit_error_disclosure.py`,
  which forces a real SMTP auth failure and compares what the client sees to
  what got logged.

## Code citations

- `db.py`: the parameterized-query pattern (`?` placeholders) follows the
  official Python docs example for `sqlite3`:
  <https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders>
- `email_utils.py`: the `smtplib`/`EmailMessage` usage pattern is adapted from
  the official Python docs SMTP example:
  <https://docs.python.org/3/library/smtplib.html#smtp-example>
- `server.py`: the `@mcp.tool()` / `@mcp.prompt()` FastMCP pattern follows the
  quickstart example in the MCP Python SDK README:
  <https://github.com/modelcontextprotocol/python-sdk>

## Project structure

```
mcp-productivity-server/
├── server.py                          # MCP server entry point: tools + prompt
├── db.py                              # SQLite helpers (parameterized queries)
├── email_utils.py                     # SMTP sending
├── security.py                        # input validation + safe error handling
├── exploits/
│   ├── exploit_sql_injection.py
│   ├── exploit_header_injection.py
│   └── exploit_error_disclosure.py
├── .env.example                       # committed (placeholders only)
├── .env                                # NOT committed (real secrets)
├── .gitignore
├── requirements.txt
├── claude_desktop_config.example.json
└── README.md
```

## Limitations

See the reflection submitted separately to Canvas for a full discussion. Briefly:
the task store is a single local SQLite file with no multi-user support, and
`send_task_reminder_email` only supports Gmail SMTP.
