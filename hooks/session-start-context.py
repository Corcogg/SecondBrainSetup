#!/usr/bin/env python3
"""
SessionStart Hook — Injects the owner's second brain memory into every Claude session.

Reads SOUL.md + USER.md + MEMORY.md + today's daily log (+ yesterday's if it exists),
then queries the second-brain vault for notes relevant to the current project domain
and appends them as a <retrieved_knowledge> XML block.

Claude Code captures this output and injects it as context at the start of the
conversation.
"""

import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import brain_config  # noqa: E402 — loads <APP_DIR>/.env as a side effect

VAULT = brain_config.VAULT_DIR
DAILY = brain_config.VAULT_DAILY
QUERY_SCRIPT = brain_config.APP_DIR / "scripts" / "query_brain.py"
PYTHON = brain_config.PYTHON

CORE_FILES = [
    ("SOUL", VAULT / "SOUL.md"),
    ("USER PROFILE", VAULT / "USER.md"),
    ("MEMORY", VAULT / "MEMORY.md"),
]

# Map cwd path fragments → (domain, n_results), from brain_config.json.
DOMAIN_MAP = brain_config.CWD_DOMAIN_MAP


def strip_empty_session_markers(text: str) -> str:
    """Drop log blocks that contain nothing but a '### [SESSION END ...]' header.

    Daily logs accumulate dozens of empty session-end markers that carry no
    information; keep only blocks with real content.
    """
    import re
    blocks = re.split(r"\n?---\n", text)
    kept = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        if re.fullmatch(r"### \[SESSION END[^\]]*\]", stripped):
            continue
        kept.append(stripped)
    return "\n\n---\n\n".join(kept)


def read_file(path: Path) -> Optional[str]:
    try:
        content = path.read_text(encoding="utf-8").strip()
        return content if content else None
    except OSError:
        return None


def detect_domain() -> tuple[Optional[str], int]:
    """
    Return (domain, n) based on the current working directory.
    Uses os.getcwd() — the hook inherits CWD from the shell that launched Claude.
    """
    cwd = os.getcwd()
    for entry in DOMAIN_MAP:
        fragment = entry.get("fragment", "")
        domain = entry.get("domain")
        n = entry.get("n", 5)
        if fragment and fragment in cwd:
            return domain, n
    return None, 5  # general: cross-domain top-5


def query_vault(domain: Optional[str], n: int) -> Optional[str]:
    """
    Call query_brain.py --xml [--domain <domain>] --n <n> as a subprocess.
    Returns the XML string, or None on any failure.
    """
    if not QUERY_SCRIPT.exists():
        return None

    # brain_config.load_dotenv() has already applied <APP_DIR>/.env, with
    # VOYAGE_API_KEY winning over any stale/empty inherited value — use the
    # resulting process env directly rather than re-parsing a dotenv file.
    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if not voyage_key:
        return None

    cmd = [PYTHON, str(QUERY_SCRIPT), "--xml", "--n", str(n)]
    if domain:
        query_text = f"{domain} decisions preferences context"
        cmd += [query_text, "--domain", domain]
    else:
        # General or system: broad cross-domain overview
        cmd += [f"{brain_config.OWNER_NAME} current projects preferences decisions"]

    env = {**os.environ, "VOYAGE_API_KEY": voyage_key}

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=8,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    return None


def main():
    sections = []

    # Inject core memory files
    for label, path in CORE_FILES:
        content = read_file(path)
        if content:
            sections.append(f"=== {label} ===\n{content}")

    # Inject today's daily log if it exists (empty session markers stripped, capped)
    today = date.today()
    today_log = DAILY / f"{today}.md"
    content = read_file(today_log)
    if content:
        content = strip_empty_session_markers(content)
    if content:
        lines = content.splitlines()
        excerpt = "\n".join(lines[-80:]) if len(lines) > 80 else content
        sections.append(f"=== TODAY'S LOG ({today}) ===\n{excerpt}")

    # Inject yesterday's daily log for continuity (same filtering)
    yesterday = today - timedelta(days=1)
    yesterday_log = DAILY / f"{yesterday}.md"
    content = read_file(yesterday_log)
    if content:
        content = strip_empty_session_markers(content)
    if content:
        # Only include the last 50 lines of yesterday — avoid bloating context
        lines = content.splitlines()
        excerpt = "\n".join(lines[-50:]) if len(lines) > 50 else content
        sections.append(f"=== YESTERDAY'S LOG ({yesterday}, last 50 lines) ===\n{excerpt}")

    # ── Vault context injection ───────────────────────────────────────────────
    domain, n = detect_domain()
    vault_xml = query_vault(domain, n)
    if vault_xml:
        label = f"VAULT CONTEXT [{domain or 'general'}]"
        sections.append(f"=== {label} ===\n{vault_xml}")

    if not sections:
        print("[Second Brain] Memory vault is empty — no context injected.", file=sys.stderr)
        sys.exit(0)

    output = "\n\n".join(sections)
    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[session-start-context] error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
