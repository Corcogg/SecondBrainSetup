#!/usr/bin/env python3
"""
PreCompact Hook — Saves important context before Claude auto-compacts the conversation.

Reads the conversation transcript, extracts key decisions/facts/code changes,
and appends them to today's daily log so nothing is lost after compaction.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import brain_config  # noqa: E402

DAILY = brain_config.VAULT_DAILY


def get_transcript_path() -> Optional[Path]:
    """Transcript path is passed via stdin as JSON or via env var."""
    # Try stdin first (Claude Code passes hook input as JSON on stdin)
    try:
        raw = sys.stdin.read().strip()
        if raw:
            data = json.loads(raw)
            path = data.get("transcript_path") or data.get("transcriptPath")
            if path:
                return Path(path)
    except (json.JSONDecodeError, OSError):
        pass

    # Fallback: env var
    env_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if env_path:
        return Path(env_path)

    return None


def extract_messages(transcript_path: Path) -> list[dict]:
    """Parse JSONL transcript into list of {role, content} dicts."""
    messages = []
    try:
        for line in transcript_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") not in ("user", "assistant"):
                    continue
                if obj.get("isSidechain"):
                    continue
                # Real content lives nested under "message"; content is either a
                # string or a list of typed blocks (text/tool_use/tool_result/thinking).
                message = obj.get("message") or {}
                role = message.get("role") or obj.get("type", "")
                content = message.get("content") or ""
                if isinstance(content, list):
                    # Extract text from content blocks
                    content = " ".join(
                        block.get("text", "") for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    )
                if role and content:
                    messages.append({"role": str(role), "content": str(content)})
            except (json.JSONDecodeError, AttributeError):
                continue
    except OSError:
        pass
    return messages


def summarize_transcript(messages: list[dict]) -> str:
    """Extract the last 20 exchanges and format as a compact flush summary."""
    if not messages:
        return ""

    # Take last 20 messages
    recent = messages[-20:]

    lines = []
    for msg in recent:
        role = msg["role"].capitalize()
        # Truncate long messages
        content = msg["content"]
        if len(content) > 300:
            content = content[:300] + "…"
        lines.append(f"**{role}:** {content}")

    return "\n".join(lines)


def append_to_daily_log(content: str) -> None:
    """Append a timestamped compact flush entry to today's daily log."""
    from datetime import datetime

    today = date.today()
    log_path = DAILY / f"{today}.md"
    DAILY.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%H:%M")
    entry = f"\n---\n### [COMPACT FLUSH {timestamp}]\n{content}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    transcript_path = get_transcript_path()
    if not transcript_path or not transcript_path.exists():
        print("[pre-compact-flush] No transcript found — skipping flush.", file=sys.stderr)
        sys.exit(0)

    messages = extract_messages(transcript_path)
    if not messages:
        sys.exit(0)

    summary = summarize_transcript(messages)
    if summary:
        append_to_daily_log(summary)
        print(f"[pre-compact-flush] Saved {len(messages)} messages to today's log.", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[pre-compact-flush] error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
