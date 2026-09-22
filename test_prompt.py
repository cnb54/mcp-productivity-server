"""
test_prompt.py
----------------
Directly calls the daily_planner_prompt() function from server.py and
prints exactly what it returns.

Why this file exists: the MCP *prompt* type is supposed to be invoked
through a chat client's UI (a slash command, an attachment picker, etc.).
This particular build of Claude Desktop doesn't expose that UI yet, and
the MCP Inspector (`mcp dev server.py`) depends on Node's `npx`, which
has been unreliable on this network. This script sidesteps both of those
client-side issues and calls the prompt function the exact same way
FastMCP would call it internally -- proving the prompt logic itself
works, independent of any particular client's UI.

Run with:  python test_prompt.py
"""

from server import daily_planner_prompt

print("Calling daily_planner_prompt() directly...\n")
print("=" * 60)
print(daily_planner_prompt())
print("=" * 60)