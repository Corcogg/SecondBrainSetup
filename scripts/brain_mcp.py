#!/usr/bin/env python3
"""
brain_mcp.py — claude-brain MCP server for the second brain.

Exposes read-only query/status tools plus a note-writing tool to Claude:
  - brain_query(query, domain, n)              → XML context block
  - brain_remember(content, title, domain, type) → writes note to vault
  - get_note(id)                                 → full markdown of a vault note
  - brain_status()                               → watcher/chroma/vault health text
  - list_domains()                               → sorted domains present in Chroma

Registered in ~/.claude/settings.json (or Claude Desktop config) as
mcpServers.claude-brain. Runs as a stdio MCP server (spawned automatically).

This server is read-only with respect to Chroma: it never upserts or deletes
vectors. brain_remember only writes vault markdown; the brain_watcher daemon
is solely responsible for embedding.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Ensure brain_config / brain_vector are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain_config  # noqa: E402 — loads <APP_DIR>/.env as a side effect
import brain_platform  # noqa: E402

from mcp.server.fastmcp import FastMCP
import voyageai

from brain_vector import (
    VAULT_ROOT,
    get_collection,
    query_brain,
    format_for_injection,
)

ALLOWED_TYPES   = {"fact", "preference", "project", "person", "moc"}
ALLOWED_DOMAINS = set(brain_config.DOMAINS)
RECONCILE_MARKER = brain_config.LAST_RECONCILE_FILE
WATCHER_SCRIPT = Path(__file__).resolve().parent / "brain_watcher.py"


def _frontmatter_stub(title: str, domain: str, note_type: str) -> str:
    """Build a minimal, valid frontmatter block honoring user-supplied type/domain.
    Watcher will backfill `summary` lazily; other tools (wikilinks, embed) run as normal."""
    if note_type not in ALLOWED_TYPES:
        note_type = "fact"
    if domain not in ALLOWED_DOMAINS:
        domain = brain_config.DOMAINS[0]
    safe_title = title.replace('"', '\\"')
    today = datetime.now().strftime("%Y-%m-%d")
    return (
        "---\n"
        f'title: "{safe_title}"\n'
        f"type: {note_type}\n"
        f"domain: {domain}\n"
        "status: seedling\n"
        'summary: ""\n'
        "tags: []\n"
        "related: []\n"
        f"created: {today}\n"
        'up: ""\n'
        "---\n\n"
    )

mcp = FastMCP("claude-brain")

# ── Lazy-init singletons ──────────────────────────────────────────────────────
# Initialized on first tool call to avoid startup latency.

_voyage: voyageai.Client | None = None
_collection = None


def _clients():
    global _voyage, _collection
    if _voyage is None:
        api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError("VOYAGE_API_KEY not set in MCP server environment")
        _voyage = voyageai.Client(api_key=api_key)
        _collection = get_collection()
    return _voyage, _collection


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def brain_query(
    query: str,
    domain: str | None = None,
    n: int = 8,
) -> str:
    """
    Query the second brain vault for notes semantically relevant to the query.

    Returns an XML-formatted <retrieved_knowledge> block containing matching
    notes with title, domain, and relevance score. Use this proactively when
    starting work on a known project, or when the user asks about a decision
    or preference that likely lives in the vault.

    Args:
        query:  Natural-language search query
        domain: Optional filter — one of the configured domains
        n:      Number of results to return (default 8, max 20)
    """
    vc, col = _clients()
    n = min(max(1, n), 20)
    hits = query_brain(vc, col, query, domain=domain, n=n)
    if not hits:
        return "<retrieved_knowledge>No relevant notes found.</retrieved_knowledge>"
    return format_for_injection(hits)


@mcp.tool()
def brain_remember(
    content: str,
    title: str,
    domain: str = brain_config.DOMAINS[0],
    note_type: str = "fact",
) -> str:
    """
    Write a new note to the second brain vault.

    The brain_watcher daemon will automatically add YAML frontmatter,
    inject wikilinks, and embed the note into the vector store within ~5 seconds.

    Args:
        content:   The full markdown body of the note
        title:     Human-readable title (used to derive the filename)
        domain:    one of the configured domains
        note_type: one of: fact, preference, project, person, moc
    """
    # Sanitize title → safe filename stem
    stem = re.sub(r"[^\w\s-]", "", title.lower())
    stem = re.sub(r"[\s]+", "_", stem.strip())[:60]
    if not stem:
        stem = "untitled_note"

    # Normalize domain, then resolve target subdirectory from config.
    if domain not in ALLOWED_DOMAINS:
        domain = brain_config.DOMAINS[0]
    subdir_name = brain_config.DOMAIN_DIRS.get(domain, domain)
    subdir = VAULT_ROOT / subdir_name
    subdir.mkdir(parents=True, exist_ok=True)

    path = subdir / f"{stem}.md"

    # Avoid overwriting an existing note
    if path.exists():
        counter = 1
        while path.exists():
            path = subdir / f"{stem}_{counter}.md"
            counter += 1

    # Prepend stub frontmatter if content doesn't already have one.
    # Pins user-supplied title/type/domain; watcher will backfill the empty summary.
    if not content.strip().startswith("---"):
        content = _frontmatter_stub(title, domain, note_type) + content

    path.write_text(content, encoding="utf-8")
    return f"Saved: {path.relative_to(VAULT_ROOT.parent)} — watcher will embed within 5 seconds."


@mcp.tool()
def get_note(id: str) -> str:
    """
    Fetch the full markdown content of a vault note by its filename stem.

    Args:
        id: The note's filename stem (no path, no extension — e.g. "example_note_stem").
            Must not contain "/" or ".." — such ids are rejected outright.

    Returns:
        The note's vault-relative path followed by its full markdown content,
        or a clear "not found" message if no note matches.
    """
    if not isinstance(id, str) or not id.strip():
        return "Not found: id must be a non-empty string."
    note_id = id.strip()
    if "/" in note_id or ".." in note_id:
        return "Not found: id must be a bare filename stem (no '/' or '..')."

    for path in VAULT_ROOT.rglob("*.md"):
        if ".obsidian" in path.parts:
            continue
        if path.stem == note_id:
            content = path.read_text(encoding="utf-8")
            return f"Path: {path.relative_to(VAULT_ROOT.parent)}\n\n{content}"

    return f"Not found: no vault note with stem '{note_id}'."


@mcp.tool()
def brain_status() -> str:
    """
    Report second brain system health: watcher process, Chroma index size,
    vault note count, and time since the last reconcile sweep.

    Useful for diagnosing whether new notes are being embedded, whether the
    watcher daemon crashed, or how stale the index might be.
    """
    lines = []

    # Watcher aliveness
    pids = brain_platform.watcher_pids(WATCHER_SCRIPT)
    if pids:
        lines.append(f"Watcher: running (pid {', '.join(pids)})")
    else:
        lines.append("Watcher: not running")

    # Chroma note count
    try:
        _, col = _clients()
        lines.append(f"Chroma notes indexed: {col.count()}")
    except Exception as e:
        lines.append(f"Chroma notes indexed: unavailable ({type(e).__name__}: {e})")

    # Vault .md file count
    try:
        vault_count = sum(
            1 for p in VAULT_ROOT.rglob("*.md") if ".obsidian" not in p.parts
        )
        lines.append(f"Vault markdown files: {vault_count}")
    except Exception as e:
        lines.append(f"Vault markdown files: unavailable ({type(e).__name__}: {e})")

    # Last reconcile timestamp
    if RECONCILE_MARKER.exists():
        try:
            ts = int(RECONCILE_MARKER.read_text(encoding="utf-8").strip())
            age_min = int((datetime.now().timestamp() - ts) / 60)
            when = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"Last reconcile: {when} ({age_min} min ago)")
        except Exception:
            mtime = datetime.fromtimestamp(RECONCILE_MARKER.stat().st_mtime)
            lines.append(f"Last reconcile: {mtime.isoformat()} (mtime fallback)")
    else:
        lines.append("Last reconcile: never")

    return "\n".join(lines)


@mcp.tool()
def list_domains() -> str:
    """
    List all domains currently present in the Chroma vector store.

    Returns a sorted, newline-separated list of unique domain values found
    in note metadata.
    """
    _, col = _clients()
    try:
        all_data = col.get(include=["metadatas"])
        domains = {
            (m or {}).get("domain", "")
            for m in (all_data.get("metadatas") or [])
        }
        domains = sorted(d for d in domains if d)
    except Exception as e:
        return f"Could not list domains: {type(e).__name__}: {e}"

    if not domains:
        return "No domains found in Chroma."
    return "\n".join(domains)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
