#!/usr/bin/env python3
"""
Stop Hook (SessionEnd) — Captures a structured session summary when a Claude session ends.

Reads the full conversation transcript and writes a summary to today's daily log,
including: files changed, decisions made, tasks completed, and questions remaining.

Stop fires after EVERY assistant turn, not once per session. So when the hook
input carries a session id, the block for that session is upserted in place
(bracketed by HTML-comment markers) instead of appended again each turn;
otherwise the daily log fills with near-duplicate copies of the session.
Without a session id the hook falls back to append-only.
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


def read_hook_input() -> dict:
    try:
        raw = sys.stdin.read().strip()
        if raw:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def get_transcript_path(hook_input: dict) -> Optional[Path]:
    path = hook_input.get("transcript_path") or hook_input.get("transcriptPath")
    if path:
        return Path(path)
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


def upsert_session_block(log_path: Path, session_id: str, block_text: str) -> None:
    """Insert-or-replace the single block for `session_id` in `log_path`.

    The LAST start marker for this session and the first end marker after it
    bound the block that is replaced; bytes outside that span are untouched.
    A start marker with no end marker after it is left alone and a new block
    is appended. The write is atomic (tmp file in the same dir, os.replace).
    """
    start_marker = f"<!-- claudebrain-session:{session_id} -->"
    end_marker = f"<!-- /claudebrain-session:{session_id} -->"
    # A transcript that quotes marker text must not plant a second marker.
    block_text = (block_text.replace("<!-- claudebrain-session:", "<!-- claudebrain-session (quoted):")
                            .replace("<!-- /claudebrain-session:", "<!-- /claudebrain-session (quoted):"))
    entry = start_marker + "\n" + block_text + "\n" + end_marker

    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = log_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = ""

    start_index = existing.rfind(start_marker)
    end_index = existing.find(end_marker, start_index) if start_index != -1 else -1
    if start_index != -1 and end_index != -1:
        new_text = existing[:start_index] + entry + existing[end_index + len(end_marker):]
    else:
        new_text = existing + "\n---\n" + entry + "\n"

    tmp_path = log_path.with_name(log_path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(new_text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp_path), str(log_path))


def main():
    session_start = datetime.now().strftime("%H:%M")

    hook_input = read_hook_input()
    session_id = hook_input.get("session_id") or hook_input.get("sessionId")
    transcript_path = get_transcript_path(hook_input)
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
    if session_id:
        upsert_session_block(DAILY / f"{date.today()}.md", str(session_id), formatted)
    else:
        append_to_daily_log(formatted)

    print(f"[session-end-flush] Session summary saved ({len(messages)} messages).", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[session-end-flush] error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
