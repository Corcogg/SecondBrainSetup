#!/usr/bin/env python3
"""
Stop Hook (SessionEnd) — Captures a structured session summary when a Claude session ends.

Reads the full conversation transcript and writes a summary to today's daily log,
including: files changed, decisions made, tasks completed, and questions remaining.
"""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import brain_config  # noqa: E402

DAILY = brain_config.VAULT_DAILY

# Per-message and per-session capture limits
MIN_MESSAGE_LENGTH = 100      # Only capture assistant messages longer than this
MAX_MESSAGE_CHARS = 800       # Max chars to include from any single message
MAX_SESSION_CHARS = 3000      # Max chars contributed by a single session

# Keywords that signal important content worth capturing
DECISION_SIGNALS = ["decided", "going with", "we'll use", "chosen", "the plan is", "architecture"]
FILE_SIGNALS = ["created", "wrote", "updated", "modified", "added", "deleted", "built"]
TASK_SIGNALS = ["done", "complete", "finished", "fixed", "resolved", "shipped"]
QUESTION_SIGNALS = ["need to", "next step", "todo", "should we", "still need", "not sure"]


def get_transcript_path() -> Optional[Path]:
    try:
        raw = sys.stdin.read().strip()
        if raw:
            data = json.loads(raw)
            path = data.get("transcript_path") or data.get("transcriptPath")
            if path:
                return Path(path)
    except (json.JSONDecodeError, OSError):
        pass

    env_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if env_path:
        return Path(env_path)

    return None


def extract_messages(transcript_path: Path) -> list[dict]:
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
                message = obj.get("message") or {}
                role = message.get("role") or obj.get("type", "")
                content = message.get("content") or ""
                if isinstance(content, list):
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


def extract_structured_summary(messages: list[dict]) -> dict:
    """Pull decisions, file changes, completed tasks, open questions, and substantive
    assistant content from the transcript."""
    decisions = []
    files_changed = []
    completed = []
    open_questions = []
    substantive = []  # All substantive assistant messages (length-gated)
    session_chars = 0
    session_truncated = False

    assistant_messages = [m for m in messages if m["role"] in ("assistant", "Assistant")]

    for msg in assistant_messages:
        content = msg["content"]
        content_lower = content.lower()

        # Truncate very long messages for signal extraction
        excerpt = content[:500] if len(content) > 500 else content

        if any(sig in content_lower for sig in DECISION_SIGNALS):
            decisions.append(excerpt[:200])

        if any(sig in content_lower for sig in FILE_SIGNALS):
            files_changed.append(excerpt[:200])

        if any(sig in content_lower for sig in TASK_SIGNALS):
            completed.append(excerpt[:150])

        if any(sig in content_lower for sig in QUESTION_SIGNALS):
            open_questions.append(excerpt[:150])

        # Capture ALL assistant messages longer than MIN_MESSAGE_LENGTH
        # (not just keyword-matched ones), respecting per-session cap.
        if len(content) > MIN_MESSAGE_LENGTH and not session_truncated:
            snippet = content[:MAX_MESSAGE_CHARS]
            if len(content) > MAX_MESSAGE_CHARS:
                snippet += "…"

            remaining = MAX_SESSION_CHARS - session_chars
            if remaining <= 0:
                session_truncated = True
            elif len(snippet) > remaining:
                substantive.append(snippet[:remaining] + "…")
                session_chars = MAX_SESSION_CHARS
                session_truncated = True
            else:
                substantive.append(snippet)
                session_chars += len(snippet)

    # Deduplicate (keep first 3 per category)
    return {
        "decisions": list(dict.fromkeys(decisions))[:3],
        "files_changed": list(dict.fromkeys(files_changed))[:3],
        "completed": list(dict.fromkeys(completed))[:3],
        "open_questions": list(dict.fromkeys(open_questions))[:3],
        "substantive": list(dict.fromkeys(substantive)),
        "session_truncated": session_truncated,
        "total_messages": len(messages),
    }


def format_summary(summary: dict, session_start: str) -> str:
    now = datetime.now().strftime("%H:%M")
    lines = [f"### [SESSION END {now} | {summary['total_messages']} messages]"]

    if summary["decisions"]:
        lines.append("\n**Decisions:**")
        for d in summary["decisions"]:
            lines.append(f"- {d}")

    if summary["files_changed"]:
        lines.append("\n**Files / Changes:**")
        for f in summary["files_changed"]:
            lines.append(f"- {f}")

    if summary["completed"]:
        lines.append("\n**Completed:**")
        for c in summary["completed"]:
            lines.append(f"- {c}")

    if summary["open_questions"]:
        lines.append("\n**Still open:**")
        for q in summary["open_questions"]:
            lines.append(f"- {q}")

    if summary["substantive"]:
        lines.append("\n**Assistant output:**")
        for s in summary["substantive"]:
            lines.append(f"- {s}")
        if summary.get("session_truncated"):
            lines.append(f"- _(session output truncated at {MAX_SESSION_CHARS} chars)_")

    return "\n".join(lines)


def append_to_daily_log(content: str) -> None:
    today = date.today()
    log_path = DAILY / f"{today}.md"
    DAILY.mkdir(parents=True, exist_ok=True)

    entry = f"\n---\n{content}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    session_start = datetime.now().strftime("%H:%M")

    transcript_path = get_transcript_path()
    if not transcript_path or not transcript_path.exists():
        print("[session-end-flush] No transcript found — skipping.", file=sys.stderr)
        sys.exit(0)

    messages = extract_messages(transcript_path)
    if not messages:
        sys.exit(0)

    summary = extract_structured_summary(messages)

    if not any(
        summary[key]
        for key in ("decisions", "files_changed", "completed", "open_questions", "substantive")
    ):
        print("[session-end-flush] Nothing substantive to capture — skipping write.", file=sys.stderr)
        sys.exit(0)

    formatted = format_summary(summary, session_start)
    append_to_daily_log(formatted)

    print(f"[session-end-flush] Session summary saved ({len(messages)} messages).", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[session-end-flush] error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
